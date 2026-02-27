import type { FollowUp } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check, Clock, CalendarPlus } from 'lucide-react';

interface FollowUpSectionProps {
  title: string;
  items: FollowUp[];
  variant: 'default' | 'destructive' | 'secondary' | 'outline';
  onComplete: (id: string) => void;
  onSnooze: (id: string) => void;
  hideActions?: boolean;
}

export function FollowUpSection({ title, items, variant, onComplete, onSnooze, hideActions }: FollowUpSectionProps) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold flex items-center gap-2">
        {title} <Badge variant={variant}>{items.length}</Badge>
      </h2>
      <div className="space-y-2">
        {items.map(f => (
          <Card key={f.id}>
            <CardContent className="pt-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{f.title}</p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                  <Clock className="h-3 w-3" />
                  {f.due_date} {f.due_time && `at ${f.due_time}`}
                </div>
                {f.notes && <p className="text-sm text-muted-foreground mt-1">{f.notes}</p>}
              </div>
              {!hideActions && (
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" title="Complete" onClick={() => onComplete(f.id)}>
                    <Check className="h-4 w-4 text-green-600" />
                  </Button>
                  <Button variant="ghost" size="icon" title="Snooze" onClick={() => onSnooze(f.id)}>
                    <CalendarPlus className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
