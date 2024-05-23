let index = 0;
let animationStopped = false;
const phrases = [
    "This is hard...  gimme a sec!",
    "Thinking...  Thinking...",
    "THINKING INTENSIFIES...",
    "Almost there...",
    "Hang on..."
];

function showNextPhrase() {
    if (animationStopped) return;
    var div = document.getElementById('aiWaiting');
    div.style.display = "block";
    div.innerHTML = phrases[index];
    setTimeout(() => {
    div.style.opacity = '1';
    div.style.transition = 'opacity 1s ease-in-out';
        setTimeout(() => {
            div.style.opacity = '0';
            div.style.transition = 'opacity 1s ease-in-out';
            index = (index + 1) % phrases.length;
            setTimeout(showNextPhrase, 1000); // Adjust timing here (1000 = 1 second)
    }, 1000); // Adjust timing here (1000 = 1 second)
    }, 100); // Adjust timing here
}

function startAnimation() {
    document.getElementById('aiWaiting').style.display = "block"
    index = 0;
    animationStopped = false;
    showNextPhrase();
}

function stopAnimation() {
    document.getElementById('aiWaiting').style.display = "none"
    animationStopped = true;
    }