// fetch real-time stats from the backend when the page loads
window.addEventListener('load', async function() {
    const statsDiv = document.getElementById('stats');
    const API_BASE = '';

    try {
        const resp = await fetch(API_BASE + '/analytics/live');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        statsDiv.innerHTML = `
            <p>Clicks (last minute): ${data.last_minute}</p>
        `;
    } catch (err) {
        console.error('failed to load stats', err);
        statsDiv.innerHTML = '<p>Unable to load stats. Is the server running?</p>';
    }
});
