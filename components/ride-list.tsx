"use client";

import { useState } from "react";
import { RideCard } from "@/components/ride-card";

// Sample ride data
const rides = [
  {
    id: 1,
    name: "Saturday Morning Social",
    distance: 35.5,
    category: "C",
    surface: "road",
    registered: 12,
    maxParticipants: 20,
    description:
      "A relaxed social ride through scenic countryside roads. Perfect for intermediate riders looking to build endurance while enjoying great company.",
    startTime: "2025-05-03T08:00:00",
    startLocation: "Central Park Entrance",
    estimatedDuration: "2.5 hours",
    elevation: 450,
    leader: "Jane Smith",
    mapUrl: "https://ridewithgps.com/routes/12345678",
    cyclingClub: "Wheelies Cycling Club",
  },
  {
    id: 2,
    name: "Tuesday Night Gravel Grinder",
    distance: 22.3,
    category: "B",
    surface: "gravel",
    registered: 8,
    maxParticipants: 12,
    description:
      "An exciting evening gravel ride exploring off-road trails and paths. Bring lights and be prepared for some technical sections.",
    startTime: "2025-04-30T18:00:00",
    startLocation: "River Trail Parking Lot",
    estimatedDuration: "1.5 hours",
    elevation: 320,
    leader: "Mike Johnson",
    mapUrl: "https://ridewithgps.com/routes/23456789",
    cyclingClub: "Dirt Demons MTB Club",
  },
  {
    id: 3,
    name: "Sunday Mountain Madness",
    distance: 18.7,
    category: "A",
    surface: "mountain",
    registered: 15,
    maxParticipants: 15,
    description:
      "A challenging mountain bike ride with technical descents and steep climbs. For experienced riders only. Helmets mandatory.",
    startTime: "2025-05-04T09:30:00",
    startLocation: "Mountain View Trailhead",
    estimatedDuration: "2 hours",
    elevation: 780,
    leader: "Alex Rodriguez",
    mapUrl: "https://ridewithgps.com/routes/34567890",
    cyclingClub: "Summit Seekers",
  },
  {
    id: 4,
    name: "Beginner Friendly Tour",
    distance: 15.2,
    category: "E",
    surface: "road",
    registered: 6,
    maxParticipants: 10,
    description:
      "A gentle introduction to group riding. We'll cover basic skills, road safety, and enjoy a leisurely pace. All bikes welcome!",
    startTime: "2025-05-02T10:00:00",
    startLocation: "Community Center",
    estimatedDuration: "1.5 hours",
    elevation: 120,
    leader: "Sarah Williams",
    mapUrl: "https://ridewithgps.com/routes/45678901",
    cyclingClub: "Pedal Pals Community Riders",
  },
];

export function RideList() {
  const [expandedRideId, setExpandedRideId] = useState<number | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedRideId(expandedRideId === id ? null : id);
  };

  return (
    <div className="grid gap-6">
      {rides.map((ride) => (
        <RideCard
          key={ride.id}
          ride={ride}
          isExpanded={expandedRideId === ride.id}
          onToggle={() => toggleExpand(ride.id)}
        />
      ))}
    </div>
  );
}
