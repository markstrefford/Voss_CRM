import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardSummary } from '@/api';
import type { DashboardSummary } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertCircle, TrendingUp, Clock, Activity } from 'lucide-react';

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardSummary()
      .then(res => setSummary(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64">Loading...</div>;
  if (!summary) return <div>Failed to load dashboard</div>;

  const pipelineData = Object.entries(summary.pipeline)
    .filter(([stage]) => !['won', 'lost'].includes(stage))
    .map(([stage, data]) => ({ stage: stage.charAt(0).toUpperCase() + stage.slice(1), ...data }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pipeline Value</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${summary.total_deal_value.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{summary.total_deals} total deals</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.overdue_count}</div>
            <p className="text-xs text-muted-foreground">follow-ups overdue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Due Today</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.todays_follow_ups.length}</div>
            <p className="text-xs text-muted-foreground">follow-ups today</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Activity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.recent_activity_count}</div>
            <p className="text-xs text-muted-foreground">interactions this week</p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline chart */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData}>
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Overdue follow-ups */}
      {summary.overdue_follow_ups.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Overdue Follow-ups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summary.overdue_follow_ups.map(f => (
                <div key={f.id} className="flex items-center justify-between p-2 rounded border">
                  <div>
                    <p className="font-medium">{f.title}</p>
                    <p className="text-sm text-muted-foreground">Due: {f.due_date}</p>
                  </div>
                  <Badge variant="destructive">Overdue</Badge>
                </div>
              ))}
            </div>
            <Link to="/follow-ups" className="text-sm text-primary mt-3 inline-block">View all follow-ups</Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
