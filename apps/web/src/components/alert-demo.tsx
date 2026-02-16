"use client";

import { useState, useEffect, useRef } from "react";

const ALERTS = [
  { severity: "critical", message: "Agent accessed .env file", icon: "\u26a0" },
  { severity: "warning", message: "Error rate exceeded 30%", icon: "\u26a0" },
  { severity: "warning", message: "Agent contacted unknown API domain", icon: "\u26a0" },
  { severity: "info", message: "47 actions per minute (unusual volume)", icon: "\u26a0" },
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
      timers.push(setTimeout(() => setVisible(i + 1), (i + 1) * 600));
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
          <span className="alert-sev">{alert.severity}</span>
        </div>
      ))}
    </div>
  );
}
