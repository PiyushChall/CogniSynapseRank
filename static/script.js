document.getElementById('analysisForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const main_url = formData.get('main_url');
    const comparison_urls = formData.get('comparison_urls').split(',').map(url => url.trim()).filter(url => url);

    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ main_url, comparison_urls })
    });

    const data = await response.json();
    const taskId = data.task_id;

    document.getElementById('statusText').textContent = 'Task started...';
    pollStatus(taskId);
});

async function pollStatus(taskId) {
    const statusText = document.getElementById('statusText');
    const resultsDiv = document.getElementById('results');

    const interval = setInterval(async () => {
        const response = await fetch(`/results/${taskId}`);
        const data = await response.json();

        if (data.status === 'Analysis Completed') {
            clearInterval(interval);
            statusText.textContent = 'Analysis Completed!';
            resultsDiv.textContent = 'Check your analysis results in server logs or API response.';
        } else {
            statusText.textContent = `Current Task: ${data.status}`;
        }
    }, 2000);
}
