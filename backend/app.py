import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import google.generativeai as genai
import pandas as pd
import random
import re

app = Flask(__name__)
CORS(app)

# --- GLOBAL MODEL AND PARAMETERS ---
model = None
DECAY_RATES = {}
SATURATION_ALPHAS = {}
MODEL_COEFFICIENTS = {}
# ---

def load_model_and_params(scenario):
    global model, DECAY_RATES, SATURATION_ALPHAS, MODEL_COEFFICIENTS

    if scenario == 'fast_decay':
        with open('model_fast_decay.pkl', 'rb') as f:
            model = pickle.load(f)
        DECAY_RATES = {'TV': 0.3, 'Radio': 0.4, 'Newspaper': 0.1}
        SATURATION_ALPHAS = {'TV': 0.7, 'Radio': 0.65, 'Newspaper': 0.55}
    elif scenario == 'slow_decay':
        with open('model_slow_decay.pkl', 'rb') as f:
            model = pickle.load(f)
        DECAY_RATES = {'TV': 0.7, 'Radio': 0.75, 'Newspaper': 0.4}
        SATURATION_ALPHAS = {'TV': 0.9, 'Radio': 0.85, 'Newspaper': 0.75}

    MODEL_COEFFICIENTS = {
        'TV': round(model.coef_[0], 2),
        'Radio': round(model.coef_[1], 2),
        'Newspaper': round(model.coef_[2], 2)
    }
    print(f"--- Switched to {scenario} model ---")

# Load the default model on startup
load_model_and_params('fast_decay')

@app.route('/switch-model', methods=['POST'])
def switch_model():
    data = request.get_json()
    scenario = data.get('scenario', 'fast_decay')
    load_model_and_params(scenario)
    return jsonify({"message": f"Successfully switched to {scenario} model."})

def transform_spend(tv_spend, radio_spend, newspaper_spend):
    tv_adstocked = tv_spend / (1 - DECAY_RATES['TV']) if (1 - DECAY_RATES['TV']) != 0 else tv_spend
    radio_adstocked = radio_spend / (1 - DECAY_RATES['Radio']) if (1 - DECAY_RATES['Radio']) != 0 else radio_spend
    newspaper_adstocked = newspaper_spend / (1 - DECAY_RATES['Newspaper']) if (1 - DECAY_RATES['Newspaper']) != 0 else newspaper_spend

    tv_saturated = tv_adstocked ** SATURATION_ALPHAS['TV']
    radio_saturated = radio_adstocked ** SATURATION_ALPHAS['Radio']
    newspaper_saturated = newspaper_adstocked ** SATURATION_ALPHAS['Newspaper']

    return [tv_saturated, radio_saturated, newspaper_saturated]

def find_optimal_allocation(total_budget, constraint=None):
    best_sales = 0
    best_allocation = {}
    for tv_percent in range(0, 101, 5):
        for radio_percent in range(0, 101 - tv_percent, 5):
            newspaper_percent = 100 - tv_percent - radio_percent
            tv_spend = total_budget * (tv_percent / 100)
            radio_spend = total_budget * (radio_percent / 100)
            newspaper_spend = total_budget * (newspaper_percent / 100)

            if isinstance(constraint, dict):
                channel = constraint.get('channel', '').lower()
                constraint_type = constraint.get('type')
                value = constraint.get('value')
                if not all([channel, constraint_type, value]): continue

                if (channel == 'tv' and ((constraint_type == 'cap' and tv_spend > value) or (constraint_type == 'floor' and tv_spend < value))) or \
                   (channel == 'radio' and ((constraint_type == 'cap' and radio_spend > value) or (constraint_type == 'floor' and radio_spend < value))) or \
                   (channel == 'newspaper' and ((constraint_type == 'cap' and newspaper_spend > value) or (constraint_type == 'floor' and newspaper_spend < value))):
                    continue

            transformed_features = transform_spend(tv_spend, radio_spend, newspaper_spend)
            features = np.array([transformed_features])
            predicted_sales = model.predict(features)[0]
            if predicted_sales > best_sales:
                best_sales = predicted_sales
                best_allocation = { "tv": tv_spend, "radio": radio_spend, "newspaper": newspaper_spend }
    return {"allocation": best_allocation, "sales": best_sales}

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    tv_spend = float(data.get('tv', 0))
    radio_spend = float(data.get('radio', 0))
    newspaper_spend = float(data.get('newspaper', 0))
    transformed_features = transform_spend(tv_spend, radio_spend, newspaper_spend)
    features = np.array([transformed_features])
    return jsonify({'predicted_sales': model.predict(features)[0]})

@app.route('/generate-challenge', methods=['POST'])
def generate_challenge():
    try:
        llm = genai.GenerativeModel('gemini-1.5-flash')
        for _ in range(3):
            challenge_budget = random.randint(800, 3200)
            constraint = None
            constraint_text = "No special constraints for this campaign."
            has_constraint = random.random() < 0.6
            if has_constraint:
                channel = random.choice(['TV', 'Radio', 'Newspaper'])
                constraint_type = random.choice(['cap', 'floor'])
                if constraint_type == 'cap':
                    value = round(random.uniform(0.1, 0.3) * challenge_budget)
                    constraint_text = f"The board has capped total campaign spending on {channel} at ${value}."
                else:
                    value = round(random.uniform(0.2, 0.4) * challenge_budget)
                    constraint_text = f"We have a special deal; we must spend at least ${value} on {channel} over the campaign."
                constraint = {'channel': channel, 'type': constraint_type, 'value': value, 'text': constraint_text}

            optimal_solution = find_optimal_allocation(challenge_budget, constraint)
            max_total_sales = optimal_solution['sales']
            realistic_goal = round((max_total_sales / 4) * 0.95, 2)

            prompt = f"""
            You are a witty, slightly cynical senior marketing strategist.
            YOUR TASK: Write a creative marketing challenge for a 4-week campaign.
            DATA: - The total campaign budget is: ${challenge_budget} - A realistic, achievable average weekly sales goal is: {realistic_goal} - This campaign's special constraint is: "{constraint_text}"
            INSTRUCTIONS: - Create a fun title and a 1-2 sentence scenario that incorporates the constraint. - The "goal" you write in your response must be to "achieve an average of at least {realistic_goal} in sales per week". - Return ONLY a valid JSON object with the keys: "title", "scenario", "goal", "budget", and "constraint". The 'constraint' key must be a JSON object like {json.dumps(constraint) if constraint else 'null'}.
            """
            response = llm.generate_content(prompt)
            clean_json_str = response.text.strip().replace('```json', '').replace('```', '')
            challenge_data = json.loads(clean_json_str, strict=False)

            constraint_from_llm = challenge_data.get('constraint')
            if (has_constraint and isinstance(constraint_from_llm, dict)) or \
               (not has_constraint and constraint_from_llm is None):
                return jsonify(challenge_data)

        raise ValueError("LLM failed to generate a valid challenge after multiple attempts.")

    except Exception as e:
        print(f"--- AN ERROR OCCURRED... ---\n{e}\n---")
        return jsonify({"error": "Failed to generate a valid challenge from the AI."}), 500

@app.route('/get-feedback', methods=['POST'])
def get_feedback():
    try:
        data = request.get_json()
        llm = genai.GenerativeModel('gemini-1.5-flash')

        challenge_data = data['challenge']
        challenge_budget = float(data['challenge_budget'])
        user_sales = data['result']['predicted_sales'] # This is already the weekly average
        goal_text = challenge_data['goal']

        constraint = challenge_data.get('constraint')
        if not isinstance(constraint, dict):
            constraint = None

        goal_numbers = re.findall(r'(\d+\.?\d*)', goal_text)
        if not goal_numbers:
            raise ValueError("Could not parse a number from the goal text.")

        numeric_goal = float(goal_numbers[0])
        goal_met = user_sales >= numeric_goal
        goal_met_text = "Yes" if goal_met else "No"

        optimal_solution = find_optimal_allocation(challenge_budget, constraint)
        optimal_weekly_sales = optimal_solution['sales'] / 4

        prompt = f"""
        You are a witty, slightly cynical senior marketing strategist.
        MODEL INSIGHTS (The secret formula):
        - Coefficients (Raw Power): TV={MODEL_COEFFICIENTS['TV']}, Radio={MODEL_COEFFICIENTS['Radio']}, Newspaper={MODEL_COEFFICIENTS['Newspaper']}. A higher number is better.
        - Saturation Exponents (Diminishing Returns): TV={SATURATION_ALPHAS['TV']}, Radio={SATURATION_ALPHAS['Radio']}, Newspaper={SATURATION_ALPHAS['Newspaper']}. A lower number means the channel's effectiveness fades FASTER.
        PERFORMANCE ANALYSIS:
        - Their average weekly sales were {user_sales:.2f}. The goal was {numeric_goal}.
        - Goal Met: {goal_met_text}.
        - The optimal strategy for this budget would have yielded average weekly sales of {optimal_weekly_sales:.2f}.
        YOUR TASK:
        1. Acknowledge their success or failure.
        2. Provide witty, constructive feedback based on the MODEL INSIGHTS.
        3. **Crucially, explain the nuance of saturation.** If they put all their money on Radio, tell them: "While Radio has a high coefficient, its low saturation exponent means you hit diminishing returns quickly. A more balanced approach is often better." If they did well with a balanced approach, praise them for not just chasing the highest coefficient.
        4. Keep your entire response to a maximum of 2 short paragraphs and under 90 words.
        Return the response ONLY as a valid JSON object with a single key: "feedback".
        """

        response = llm.generate_content(prompt)
        clean_json_str = response.text.strip().replace('```json', '').replace('```', '')
        feedback_data = json.loads(clean_json_str, strict=False)
        feedback_data['success'] = goal_met

        return jsonify(feedback_data)
    except Exception as e:
        print(f"--- AN ERROR OCCURRED WHILE GETTING FEEDBACK ---\nError Type: {type(e)}\nError Details: {e}\n----------------------------------------------------")
        return jsonify({"error": "Failed to get feedback from AI."}), 500

if __name__ == '__main__':
    app.run(debug=True)