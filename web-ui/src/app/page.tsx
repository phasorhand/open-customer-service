import { StatsCards } from "@/components/stats-cards";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <StatsCards />
    </div>
  );
}
