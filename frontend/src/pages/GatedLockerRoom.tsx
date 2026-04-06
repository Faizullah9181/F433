import { useState } from "react";
import { LockerRoomGate } from "./LockerRoomGate";
import { TunnelTalk } from "./TunnelTalk";

const GATE_KEY = "f433_locker_room_pass";

export function GatedLockerRoom() {
  const [passed, setPassed] = useState(() => {
    const stored = sessionStorage.getItem(GATE_KEY);
    return stored === "true";
  });

  const handlePass = () => {
    sessionStorage.setItem(GATE_KEY, "true");
    setPassed(true);
  };

  if (!passed) {
    return <LockerRoomGate onPass={handlePass} />;
  }

  return <TunnelTalk />;
}
