import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface SnoozeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  snoozeDate: string;
  onSnoozeDateChange: (date: string) => void;
  onConfirm: () => void;
}

export function SnoozeDialog({ open, onOpenChange, snoozeDate, onSnoozeDateChange, onConfirm }: SnoozeDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Snooze Follow-up</DialogTitle></DialogHeader>
        <div className="space-y-2">
          <Label>New Due Date</Label>
          <Input type="date" value={snoozeDate} onChange={e => onSnoozeDateChange(e.target.value)} />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onConfirm} disabled={!snoozeDate}>Snooze</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
