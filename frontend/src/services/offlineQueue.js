
const STORAGE_KEY = "maatricare_offline_queue";

export function queueOfflineItem(type, payload) {
  const existingQueue = getOfflineQueue();

  const newItem = {
    id: `OFFLINE-${Date.now()}`,
    type,
    payload,
    createdAt: new Date().toISOString(),
    status: "pending"
  };

  existingQueue.push(newItem);

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(existingQueue)
  );

  return newItem;
}

export function getOfflineQueue() {
  try {
    return JSON.parse(
      localStorage.getItem(STORAGE_KEY) || "[]"
    );
  } catch {
    return [];
  }
}

export function removeOfflineItem(itemId) {
  const updatedQueue = getOfflineQueue().filter(
    (item) => item.id !== itemId
  );

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(updatedQueue)
  );
}

export function clearOfflineQueue() {
  localStorage.removeItem(STORAGE_KEY);
}
