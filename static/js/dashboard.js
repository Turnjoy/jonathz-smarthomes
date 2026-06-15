async function sendDeviceCommand(deviceId, action) {
  const response = await fetch('/api/device/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, action })
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || 'Device command failed');
  }
  return payload;
}

function nextOptimisticState(currentState, action) {
  if (action === 'TOGGLE') {
    return currentState === 'ON' ? 'OFF' : 'ON';
  }
  if (['ON', 'OFF', 'OPEN', 'CLOSE', 'START', 'STOP'].includes(action)) {
    return action;
  }
  return currentState;
}

function setCardState(card, state) {
  const stateNode = card.querySelector('[data-state]');
  const toggle = card.querySelector('.toggle-switch');
  if (stateNode) {
    stateNode.textContent = state;
  }
  if (toggle) {
    toggle.classList.toggle('is-on', state === 'ON');
  }
}

document.addEventListener('click', async (event) => {
  const control = event.target.closest('[data-action]');
  if (!control) {
    return;
  }

  const card = control.closest('[data-device-id]');
  if (!card) {
    return;
  }

  const deviceId = card.dataset.deviceId;
  const action = control.dataset.action;
  const currentState = card.querySelector('[data-state]')?.textContent.trim() || '';
  control.disabled = true;

  try {
    await sendDeviceCommand(deviceId, action);
    setCardState(card, nextOptimisticState(currentState, action));
  } catch (error) {
    window.alert(error.message);
  } finally {
    control.disabled = false;
  }
});

async function refreshDeviceStatuses() {
  const response = await fetch('/api/device/status');
  if (!response.ok) {
    return;
  }
  const statuses = await response.json();
  document.querySelectorAll('[data-device-id]').forEach((card) => {
    const status = statuses[card.dataset.deviceId];
    if (status?.state) {
      setCardState(card, status.state);
    }
  });
}

window.setInterval(refreshDeviceStatuses, 5000);
