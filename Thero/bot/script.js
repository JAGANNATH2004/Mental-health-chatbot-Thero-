const responses = {
    "sad": "I'm sorry you're feeling this way. Try taking deep breaths and focusing on something positive. You're not alone. ❤️",
    "depressed": "I understand that things might be tough. Talking to someone you trust or engaging in activities you enjoy can help.",
    "stressed": "Take a break and try some deep breathing. Inhale for 4 seconds, hold for 4, and exhale for 4.",
    "anxious": "Try grounding yourself: Name 5 things you can see, 4 things you can touch, 3 things you hear, 2 things you smell, and 1 thing you taste.",
    "alone": "You are not alone. I'm here for you, and there are people who care about you. Reach out to a friend or loved one. 💙",
    "help": "If you need urgent help, please talk to someone you trust or contact a mental health professional.",
    "default": "I'm here to support you. Try expressing your feelings, and I'll do my best to help."
};

function getBotResponse(userMessage) {
    userMessage = userMessage.toLowerCase();
    for (let keyword in responses) {
        if (userMessage.includes(keyword)) {
            return responses[keyword];
        }
    }
    return responses["default"];
}

function sendMessage() {
    let inputField = document.getElementById("user-input");
    let userMessage = inputField.value.trim();
    if (userMessage === "") return;

    displayMessage("You: " + userMessage, "user-message");
    
    setTimeout(() => {
        let botResponse = getBotResponse(userMessage);
        displayMessage("Bot: " + botResponse, "bot-message");
    }, 500);
    
    inputField.value = "";
}

function displayMessage(message, className) {
    let chatBox = document.getElementById("chat-box");
    let messageDiv = document.createElement("div");
    messageDiv.textContent = message;
    messageDiv.classList.add(className);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}
