"use client";
import { useState } from "react";
import {
  Calendar,
  MapPin,
  Clock,
  ArrowUp,
  Users,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Share2,
  CalendarIcon,
  Flag,
  UserPlus,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Define the ride type
type Ride = {
  id: number;
  name: string;
  distance: number;
  category: string;
  surface: string;
  registered: number;
  maxParticipants: number;
  description: string;
  startTime: string;
  startLocation: string;
  estimatedDuration: string;
  elevation: number;
  leader: string;
  mapUrl: string;
  cyclingClub: string;
};

type RideCardProps = {
  ride: Ride;
  isExpanded: boolean;
  onToggle: () => void;
};

export function RideCard({ ride, isExpanded, onToggle }: RideCardProps) {
  const [isRegistering, setIsRegistering] = useState(false);

  // Get surface icon
  const getSurfaceIcon = (surface: string) => {
    switch (surface.toLowerCase()) {
      case "road":
        return "🛣️";
      case "mountain":
        return "⛰️";
      case "gravel":
        return "🪨";
      default:
        return "🚲";
    }
  };

  // Get category color
  const getCategoryColor = (category: string) => {
    switch (category.toUpperCase()) {
      case "A":
        return "bg-red-500";
      case "B":
        return "bg-orange-500";
      case "C":
        return "bg-yellow-500";
      case "D":
        return "bg-green-500";
      case "E":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Format short date (for abbreviated view)
  const formatShortDate = (dateString: string) => {
    const date = new Date(dateString);
    return (
      date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }) +
      " • " +
      date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
    );
  };

  const handleRegister = () => {
    setIsRegistering(true);
    // Simulate API call
    setTimeout(() => {
      setIsRegistering(false);
      alert(`You've registered for ${ride.name}!`);
    }, 1000);
  };

  return (
    <Card
      className={`transition-all duration-300 ${
        isExpanded ? "shadow-lg" : "hover:shadow-md"
      }`}
    >
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="cursor-pointer" onClick={onToggle}>
            <CardTitle className="text-xl font-bold">{ride.name}</CardTitle>
            <div className="text-sm text-muted-foreground mt-0.5">
              Hosted by {ride.cyclingClub}
            </div>
            <CardDescription className="flex items-center gap-1 mt-2">
              <span>{ride.distance} miles</span>
              <span className="mx-1">•</span>
              <span>
                {getSurfaceIcon(ride.surface)} {ride.surface}
              </span>
            </CardDescription>
            <div className="flex items-center mt-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4 mr-1" />
              {formatShortDate(ride.startTime)}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full ${getCategoryColor(
                ride.category,
              )} flex items-center justify-center text-white font-bold`}
            >
              {ride.category}
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Actions</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleRegister}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Register for ride
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Share2 className="h-4 w-4 mr-2" />
                  Share ride
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <CalendarIcon className="h-4 w-4 mr-2" />
                  Add to calendar
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Flag className="h-4 w-4 mr-2" />
                  Report issue
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-2">
        <div
          className="flex justify-between items-center cursor-pointer"
          onClick={onToggle}
        >
          <div className="flex items-center gap-1">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              {ride.registered}/{ride.maxParticipants} riders
            </span>
          </div>
          <Progress
            value={(ride.registered / ride.maxParticipants) * 100}
            className="w-24 h-2"
          />
        </div>

        {!isExpanded && (
          <div className="mt-4 flex justify-between items-center">
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleRegister();
              }}
              disabled={isRegistering}
            >
              {isRegistering ? "Registering..." : "Register Now"}
            </Button>
            <button
              className="text-sm text-muted-foreground flex items-center gap-1 hover:text-foreground"
              onClick={(e) => {
                e.stopPropagation();
                onToggle();
              }}
            >
              <ChevronDown className="h-4 w-4" />
              <span>View Details</span>
            </button>
          </div>
        )}
      </CardContent>

      {isExpanded && (
        <>
          <CardContent className="border-t pt-4">
            <div className="grid gap-4">
              <p className="text-sm">{ride.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{formatDate(ride.startTime)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{ride.startLocation}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{ride.estimatedDuration}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ArrowUp className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {ride.elevation} ft elevation gain
                  </span>
                </div>
              </div>

              <div className="mt-2">
                <h4 className="text-sm font-medium mb-2">Ride Leader</h4>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    {ride.leader.charAt(0)}
                  </div>
                  <span>{ride.leader}</span>
                </div>
              </div>

              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Route Map</h4>
                <div className="bg-muted rounded-md p-4 h-[300px] flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-2">
                      Map from{" "}
                      {ride.mapUrl.includes("ridewithgps")
                        ? "Ride with GPS"
                        : "Strava"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      The actual map would be embedded here from {ride.mapUrl}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <Button
                  className="w-full"
                  onClick={handleRegister}
                  disabled={isRegistering}
                >
                  {isRegistering ? "Registering..." : "Register for this Ride"}
                </Button>
              </div>
            </div>
          </CardContent>

          <CardFooter className="pt-2 flex justify-end">
            <button
              onClick={onToggle}
              className="text-sm text-muted-foreground flex items-center gap-1 hover:text-foreground"
            >
              <ChevronUp className="h-4 w-4" />
              <span>Collapse</span>
            </button>
          </CardFooter>
        </>
      )}

      {!isExpanded && null}
    </Card>
  );
}
