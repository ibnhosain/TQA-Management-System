/* তারবিয়াতুল কুরআন একাডেমি — Service Worker
   কাজ: (১) PWA ইনস্টলযোগ্য করা (২) ব্রাউজার/ট্যাব বন্ধ থাকলেও Web Push নোটিফিকেশন দেখানো */

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// সার্ভার থেকে পুশ এলে সিস্টেম নোটিফিকেশন দেখানো — অ্যাপ/ট্যাব বন্ধ থাকলেও কাজ করে
self.addEventListener("push", (event) => {
  let data = { title: "তারবিয়াতুল কুরআন একাডেমি", body: "", url: "/" };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch {
    /* উপেক্ষা */
  }
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/icon-192.png",
      badge: "/icon-192.png",
      data: { url: data.url || "/" },
      vibrate: [400, 150, 400],
    }),
  );
});

// নোটিফিকেশনে ক্লিক করলে অ্যাপ খোলা/ফোকাস করা
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ("focus" in client) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    }),
  );
});
