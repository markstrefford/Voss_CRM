import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getActionFeed } from '@/api';
import type { ActionFeed, ActionFeedFollowUpItem, ActionFeedContactItem, ActionFeedDealItem } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertCircle,
  TrendingUp,
  AlertTriangle,
  Send,
  Users,
  MessageCircle,
  Clock,
  DollarSign,
} from 'lucide-react';

// --- Local components ---

function QueueCard({
  title,
  icon: Icon,
  color,
  count,
  viewAllLink,
  viewAllLabel,
  children,
}: {
  title: string;
  icon: React.ElementType;
  color: 'red' | 'green' | 'amber' | 'blue';
  count: number;
  viewAllLink: string;
  viewAllLabel: string;
  children: React.ReactNode;
}) {
  const colorMap = {
    red: 'text-red-600 bg-red-50 border-red-200',
    green: 'text-green-600 bg-green-50 border-green-200',
    amber: 'text-amber-600 bg-amber-50 border-amber-200',
    blue: 'text-blue-600 bg-blue-50 border-blue-200',
  };
  const badgeColorMap = {
    red: 'bg-red-100 text-red-700',
    green: 'bg-green-100 text-green-700',
    amber: 'bg-amber-100 text-amber-700',
    blue: 'bg-blue-100 text-blue-700',
  };

  return (
    <Card className={`border ${colorMap[color]}`}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5" />
          <CardTitle className="text-base">{title}</CardTitle>
        </div>
        {count > 0 && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badgeColorMap[color]}`}>
            {count}
          </span>
        )}
      </CardHeader>
      <CardContent>
        {children}
        <Link
          to={viewAllLink}
          className="text-sm font-medium mt-3 inline-block hover:underline"
        >
          {viewAllLabel} &rarr;
        </Link>
      </CardContent>
    </Card>
  );
}

function FollowUpRow({ item }: { item: ActionFeedFollowUpItem }) {
  return (
    <Link
      to={`/contacts/${item.contact_id}`}
      className="flex items-center justify-between p-2 rounded hover:bg-white/60 transition-colors"
    >
      <div className="min-w-0">
        <p className="font-medium text-sm truncate">{item.title}</p>
        <p className="text-xs text-muted-foreground truncate">
          {item.contact_name}{item.company_name ? ` - ${item.company_name}` : ''}
        </p>
      </div>
      <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
        {item.due_date}{item.due_time ? ` ${item.due_time}` : ''}
      </span>
    </Link>
  );
}

function ContactRow({ item }: { item: ActionFeedContactItem }) {
  return (
    <Link
      to={`/contacts/${item.id}`}
      className="flex items-center justify-between p-2 rounded hover:bg-white/60 transition-colors"
    >
      <div className="min-w-0">
        <p className="font-medium text-sm truncate">{item.name}</p>
        <p className="text-xs text-muted-foreground truncate">
          {item.company_name}{item.role ? ` - ${item.role}` : ''}
        </p>
      </div>
      <Badge variant="secondary" className="text-xs whitespace-nowrap ml-2 shrink-0">
        {item.reason}
      </Badge>
    </Link>
  );
}

function DealRow({ item }: { item: ActionFeedDealItem }) {
  return (
    <Link
      to="/deals"
      className="flex items-center justify-between p-2 rounded hover:bg-white/60 transition-colors"
    >
      <div className="min-w-0">
        <p className="font-medium text-sm truncate">{item.title}</p>
        <p className="text-xs text-muted-foreground truncate">
          {item.contact_name}{item.company_name ? ` - ${item.company_name}` : ''}
        </p>
      </div>
      <div className="flex items-center gap-2 ml-2 shrink-0">
        <Badge variant="outline" className="text-xs">{item.stage}</Badge>
        <span className="text-xs text-muted-foreground">{item.days_stale}d stale</span>
      </div>
    </Link>
  );
}

function EmptyQueue({ message }: { message: string }) {
  return <p className="text-sm text-muted-foreground py-2">{message}</p>;
}

// --- Main dashboard ---

export function DashboardPage() {
  const [feed, setFeed] = useState<ActionFeed | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getActionFeed()
      .then(res => setFeed(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64">Loading...</div>;
  if (!feed) return <div>Failed to load dashboard</div>;

  const { stats, action_required, momentum, at_risk, ready_to_reach_out } = feed;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Contacts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_active_contacts}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">In Conversation</CardTitle>
            <MessageCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.in_conversation}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Follow-ups This Week</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.follow_ups_this_week}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pipeline Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.pipeline_value > 0 ? `$${stats.pipeline_value.toLocaleString()}` : '$0'}
            </div>
            <p className="text-xs text-muted-foreground">{stats.deals_in_pipeline} deals</p>
          </CardContent>
        </Card>
      </div>

      {/* Action Required (red) */}
      <QueueCard
        title="Action Required"
        icon={AlertCircle}
        color="red"
        count={action_required.overdue_total + action_required.due_today_total}
        viewAllLink="/follow-ups"
        viewAllLabel="View all follow-ups"
      >
        {action_required.overdue_follow_ups.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-red-700 uppercase mb-1">
              Overdue ({action_required.overdue_total})
            </p>
            <div className="space-y-0.5">
              {action_required.overdue_follow_ups.map(f => (
                <FollowUpRow key={f.id} item={f} />
              ))}
            </div>
          </div>
        )}
        {action_required.due_today.length > 0 && (
          <div className="mb-1">
            <p className="text-xs font-semibold text-red-700 uppercase mb-1">
              Due Today ({action_required.due_today_total})
            </p>
            <div className="space-y-0.5">
              {action_required.due_today.map(f => (
                <FollowUpRow key={f.id} item={f} />
              ))}
            </div>
          </div>
        )}
        {action_required.overdue_follow_ups.length === 0 && action_required.due_today.length === 0 && (
          <EmptyQueue message="No overdue or due-today follow-ups. You're on top of things!" />
        )}
      </QueueCard>

      {/* Momentum (green) */}
      <QueueCard
        title="Momentum"
        icon={TrendingUp}
        color="green"
        count={momentum.inbound_recent_total + momentum.no_follow_up_scheduled_total}
        viewAllLink="/contacts?engagement_stage=active"
        viewAllLabel="View active contacts"
      >
        {momentum.inbound_recent.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-green-700 uppercase mb-1">
              Inbound Replies ({momentum.inbound_recent_total})
            </p>
            <div className="space-y-0.5">
              {momentum.inbound_recent.map(c => (
                <ContactRow key={c.id} item={c} />
              ))}
            </div>
          </div>
        )}
        {momentum.no_follow_up_scheduled.length > 0 && (
          <div className="mb-1">
            <p className="text-xs font-semibold text-green-700 uppercase mb-1">
              Engaged, No Follow-up ({momentum.no_follow_up_scheduled_total})
            </p>
            <div className="space-y-0.5">
              {momentum.no_follow_up_scheduled.map(c => (
                <ContactRow key={c.id} item={c} />
              ))}
            </div>
          </div>
        )}
        {momentum.inbound_recent.length === 0 && momentum.no_follow_up_scheduled.length === 0 && (
          <EmptyQueue message="No recent inbound activity. Time to follow up!" />
        )}
      </QueueCard>

      {/* At Risk (amber) */}
      <QueueCard
        title="At Risk"
        icon={AlertTriangle}
        color="amber"
        count={at_risk.going_cold_total + at_risk.stale_deals_total}
        viewAllLink="/contacts?engagement_stage=nurturing"
        viewAllLabel="View nurturing contacts"
      >
        {at_risk.going_cold.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-amber-700 uppercase mb-1">
              Going Cold ({at_risk.going_cold_total})
            </p>
            <div className="space-y-0.5">
              {at_risk.going_cold.map(c => (
                <ContactRow key={c.id} item={c} />
              ))}
            </div>
          </div>
        )}
        {at_risk.stale_deals.length > 0 && (
          <div className="mb-1">
            <p className="text-xs font-semibold text-amber-700 uppercase mb-1">
              Stale Deals ({at_risk.stale_deals_total})
            </p>
            <div className="space-y-0.5">
              {at_risk.stale_deals.map(d => (
                <DealRow key={d.id} item={d} />
              ))}
            </div>
          </div>
        )}
        {at_risk.going_cold.length === 0 && at_risk.stale_deals.length === 0 && (
          <EmptyQueue message="Nothing at risk right now. Keep up the engagement!" />
        )}
      </QueueCard>

      {/* Ready to Reach Out (blue) */}
      <QueueCard
        title="Ready to Reach Out"
        icon={Send}
        color="blue"
        count={ready_to_reach_out.new_contacts_total}
        viewAllLink="/contacts?engagement_stage=new"
        viewAllLabel="View all new contacts"
      >
        {ready_to_reach_out.new_contacts.length > 0 ? (
          <div className="space-y-0.5">
            {ready_to_reach_out.new_contacts.map(c => (
              <ContactRow key={c.id} item={c} />
            ))}
          </div>
        ) : (
          <EmptyQueue message="No new contacts waiting for outreach." />
        )}
      </QueueCard>

      {/* Safety net links */}
      <div className="flex gap-4 text-sm pt-2">
        <Link to="/contacts" className="text-muted-foreground hover:text-foreground hover:underline">
          View all contacts &rarr;
        </Link>
        <Link to="/deals" className="text-muted-foreground hover:text-foreground hover:underline">
          View all deals &rarr;
        </Link>
      </div>
    </div>
  );
}
