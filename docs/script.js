// We wrap the entire script in window.onload
window.onload = function() {
    const API_URL = 'https://mmm-game-api.onrender.com';

    const analystAvatars = {
        sandbox: 'https://lottie.host/f838ed1e-c300-471a-8bc9-1cfd7ca37b65/GXxRI5HPqF.json',
        thinking: 'https://lottie.host/416f6ee8-78d8-4c65-82ab-7819f84ce0d3/zI0Q36fzAL.json',
        success: 'https://lottie.host/0774f236-83b6-4974-ac69-d36017856c1c/3mHzJxpsuF.json',
        failure: 'https://lottie.host/2c9d6f2b-5c25-4325-8c0b-2d309aeb2dbd/rXw6X2a65P.json'
    };

    // Get all DOM elements
    const analystAvatar = document.getElementById('analyst-avatar');
    const sandboxRadio = document.getElementById('sandbox-mode-radio');
    const challengeRadio = document.getElementById('challenge-mode-radio');
    const analystSandboxView = document.getElementById('analyst-sandbox-view');
    const analystChallengeView = document.getElementById('analyst-challenge-view');
    const totalBudgetSlider = document.getElementById('total-budget');
    const totalBudgetValue = document.getElementById('total-budget-value');
    const tvSlider = document.getElementById('tv-slider');
    const radioSlider = document.getElementById('radio-slider');
    const newspaperSlider = document.getElementById('newspaper-slider');
    const tvValue = document.getElementById('tv-value');
    const radioValue = document.getElementById('radio-value');
    const newspaperValue = document.getElementById('newspaper-value');
    const allocationTotal = document.getElementById('allocation-total');
    const simulateBtn = document.getElementById('simulate-btn');
    const salesOutput = document.getElementById('sales-output');
    const weeklySalesOutput = document.getElementById('weekly-sales-output');
    const newChallengeBtn = document.getElementById('new-challenge-btn');
    const challengeDisplay = document.getElementById('challenge-display');
    const challengeTitle = document.getElementById('challenge-title');
    const challengeScenario = document.getElementById('challenge-scenario');
    const challengeConstraint = document.getElementById('challenge-constraint');
    const challengeGoal = document.getElementById('challenge-goal');
    const feedbackDisplay = document.getElementById('feedback-display');
    const feedbackText = document.getElementById('feedback-text');
    const aboutBtn = document.getElementById('about-btn');
    const modalOverlay = document.getElementById('modal-overlay');
    const closeBtn = document.getElementById('close-btn');

    let currentChallenge = null;

    function setMode(mode) {
        if (mode === 'sandbox') {
            analystSandboxView.classList.remove('hidden');
            analystChallengeView.classList.add('hidden');
            challengeDisplay.classList.add('hidden');
            feedbackDisplay.classList.add('hidden');
            totalBudgetSlider.disabled = false;
            //analystAvatar.src = analystAvatars.thinking;
            analystAvatar.load(analystAvatars.sandbox);
            analystAvatar.style.borderColor = 'var(--primary-color)';
            sandboxRadio.checked = true;
        } else {
            analystSandboxView.classList.add('hidden');
            analystChallengeView.classList.remove('hidden');
            challengeRadio.checked = true;
        }
    }
    sandboxRadio.addEventListener('change', () => setMode('sandbox'));
    challengeRadio.addEventListener('change', () => setMode('challenge'));

    function updateDisplays() {
        const budget = parseFloat(totalBudgetSlider.value);
        totalBudgetValue.textContent = budget;
        const tvPercent = parseInt(tvSlider.value);
        tvValue.textContent = tvPercent;
        document.getElementById('tv-spend-value').textContent = `$${(budget * tvPercent / 100).toFixed(0)}`;
        const radioPercent = parseInt(radioSlider.value);
        radioValue.textContent = radioPercent;
        document.getElementById('radio-spend-value').textContent = `$${(budget * radioPercent / 100).toFixed(0)}`;
        const newspaperPercent = parseInt(newspaperSlider.value);
        newspaperValue.textContent = newspaperPercent;
        document.getElementById('newspaper-spend-value').textContent = `$${(budget * newspaperPercent / 100).toFixed(0)}`;
        const totalPercent = tvPercent + radioPercent + newspaperPercent;
        allocationTotal.textContent = totalPercent;
        allocationTotal.classList.toggle('error', totalPercent !== 100);
    }
    [totalBudgetSlider, tvSlider, radioSlider, newspaperSlider].forEach(slider => {
        slider.addEventListener('input', updateDisplays);
    });

    newChallengeBtn.addEventListener('click', () => {
        newChallengeBtn.textContent = 'Generating...';
        newChallengeBtn.disabled = true;
        challengeDisplay.classList.add('hidden');
        feedbackDisplay.classList.add('hidden');
        //analystAvatar.src = analystAvatars.thinking;
        analystAvatar.load(analystAvatars.thinking);
        analystAvatar.style.borderColor = 'var(--primary-color)';
        challengeTitle.textContent = '';
        challengeScenario.textContent = '';
        challengeConstraint.textContent = '';
        challengeGoal.textContent = '';

        fetch(`${API_URL}/generate-challenge`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.error) { throw new Error(data.error); }
                currentChallenge = data;
                challengeTitle.textContent = data.title;
                challengeScenario.textContent = data.scenario;
                challengeGoal.innerHTML = `<strong>Your Goal:</strong> ${data.goal}`;
                totalBudgetSlider.value = data.budget;
                totalBudgetSlider.disabled = true;
                resetSliderConstraints();
                if (data.constraint && data.constraint.channel) {
                    applyConstraint(data.constraint);
                    challengeConstraint.innerHTML = `<strong>Constraint:</strong> ${data.constraint.text}`;
                } else {
                    challengeConstraint.innerHTML = '';
                }
                updateDisplays();
                challengeDisplay.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error generating challenge:', error);
                challengeScenario.textContent = 'Failed to load a challenge. Please try again.';
                challengeDisplay.classList.remove('hidden');
            })
            .finally(() => {
                newChallengeBtn.textContent = 'Give Me a Challenge';
                newChallengeBtn.disabled = false;
            });
    });

    function resetSliderConstraints() {
        [tvSlider, radioSlider, newspaperSlider].forEach(slider => {
            slider.min = 0;
            slider.max = 100;
        });
    }

    function applyConstraint(constraint) {
        const budget = parseFloat(totalBudgetSlider.value);
        const channelSlider = document.getElementById(`${constraint.channel.toLowerCase()}-slider`);
        if (!channelSlider) return;
        const valueInPercent = Math.round((constraint.value / budget) * 100);
        if (constraint.type === 'cap') {
            channelSlider.max = valueInPercent;
            if (parseInt(channelSlider.value) > valueInPercent) channelSlider.value = valueInPercent;
        } else if (constraint.type === 'floor') {
            channelSlider.min = valueInPercent;
            if (parseInt(channelSlider.value) < valueInPercent) channelSlider.value = valueInPercent;
        }
    }

    simulateBtn.addEventListener('click', runSimulation);

    function runSimulation() {
        const totalPercent = parseInt(tvSlider.value) + parseInt(radioSlider.value) + parseInt(newspaperSlider.value);
        if (totalPercent !== 100) {
            alert('Total allocation must be exactly 100%.');
            return;
        }
        salesOutput.textContent = '...';
        weeklySalesOutput.textContent = '...';
        if (challengeRadio.checked) feedbackDisplay.classList.add('hidden');

        const budget = parseFloat(totalBudgetSlider.value);
        const tvSpend = budget * (parseFloat(tvSlider.value) / 100);
        const radioSpend = budget * (parseFloat(radioSlider.value) / 100);
        const newspaperSpend = budget * (parseFloat(newspaperSlider.value) / 100);
        const payload = { tv: tvSpend, radio: radioSpend, newspaper: newspaperSpend };

        fetch(`${API_URL}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            const totalSales = data.predicted_sales;
            const weeklySales = totalSales / 4;
            salesOutput.textContent = totalSales.toFixed(2);
            weeklySalesOutput.textContent = weeklySales.toFixed(2);

            if (challengeRadio.checked && currentChallenge) {
                feedbackDisplay.classList.remove('hidden');
                feedbackText.textContent = 'The analyst is thinking...';
                //analystAvatar.src = analystAvatars.thinking;
                analystAvatar.load(analystAvatars.thinking);
                analystAvatar.style.borderColor = 'var(--primary-color)';
                const feedbackPayload = {
                    challenge: currentChallenge,
                    user_spend: { tv: tvSpend, radio: radioSpend, newspaper: newspaperSpend },
                    result: { predicted_sales: weeklySales },
                    challenge_budget: budget
                };
                return fetch(`${API_URL}/get-feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(feedbackPayload)
                });
            }
        })
        .then(response => { if (response) { return response.json(); } })
        .then(data => {
            if (data && data.feedback) {
                feedbackText.textContent = data.feedback;
                if (data.success) {
                    //analystAvatar.src = analystAvatars.success;
                    analystAvatar.load(analystAvatars.success);
                    analystAvatar.style.borderColor = 'var(--success-color)';
                } else {
                    //analystAvatar.src = analystAvatars.failure;
                    analystAvatar.load(analystAvatars.failure);
                    analystAvatar.style.borderColor = 'var(--failure-color)';
                }
            } else if (data && data.error) {
                feedbackText.textContent = `Error getting feedback: ${data.error}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            salesOutput.textContent = 'Error!';
            if(challengeRadio.checked) feedbackText.textContent = 'Could not get feedback due to an error.';
        });
    }

    aboutBtn.addEventListener('click', () => modalOverlay.classList.add('visible'));
    closeBtn.addEventListener('click', () => modalOverlay.classList.remove('visible'));
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            modalOverlay.classList.remove('visible');
        }
    });

    // Initialize
    //analystAvatar.src = analystAvatars.thinking;
    setMode('sandbox');
    updateDisplays();
};