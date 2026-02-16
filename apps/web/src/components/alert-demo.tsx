"use client";

import { useState, useEffect, useRef } from "react";

const ALERTS = [
  { severity: "critical", message: "Agent accessed .env credentials file", icon: "\u26a0", sev: "critical" },
  { severity: "warning", message: "Error rate exceeded 30% (14 of 41 actions failed)", icon: "\u26a0", sev: "warning" },
  { severity: "warning", message: "47 actions per minute \u2014 unusual volume detected", icon: "\u26a0", sev: "warning" },
  { severity: "info", message: "New external API domain contacted: unknown-service.io", icon: "\u2139", sev: "info" },
];

export function AlertDemo() {
  const [visible, setVisible] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started) {
          setStarted(true);
        }
      },
      { threshold: 0.4 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    ALERTS.forEach((_, i) => {
      timers.push(setTimeout(() => setVisible(i + 1), (i + 1) * 500));
    });
    return () => timers.forEach(clearTimeout);
  }, [started]);

  return (
    <div className="alert-demo" ref={ref}>
      {ALERTS.slice(0, visible).map((alert, i) => (
        <div
          key={i}
          className={`alert-entry alert-${alert.severity}`}
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <span className="alert-icon">{alert.icon}</span>
          <span className="alert-msg">{alert.message}</span>
          <span className="alert-sev">{alert.sev}</span>
        </div>
      ))}
    </div>
  );
}
