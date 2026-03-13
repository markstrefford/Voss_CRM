import { useEffect, useState } from 'react';
import { getFollowUps, getContacts, createFollowUp, updateFollowUp, completeFollowUp, snoozeFollowUp } from '@/api';
import type { FollowUp, Contact } from '@/types';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FollowUpSection } from '@/components/shared/FollowUpSection';
import { SnoozeDialog } from '@/components/shared/SnoozeDialog';
import { Plus } from 'lucide-react';

export function FollowUpsPage() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editFollowUp, setEditFollowUp] = useState<FollowUp | null>(null);
  const [snoozeId, setSnoozeId] = useState<string | null>(null);
  const [snoozeDate, setSnoozeDate] = useState('');

  const load = () => {
    Promise.all([getFollowUps(), getContacts()])
      .then(([f, c]) => { setFollowUps(f.data); setContacts(c.data); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleComplete = async (id: string) => {
    await completeFollowUp(id);
    load();
  };

  const handleSnooze = async () => {
    if (snoozeId && snoozeDate) {
      await snoozeFollowUp(snoozeId, snoozeDate);
      setSnoozeId(null);
      setSnoozeDate('');
      load();
    }
  };

  const today = new Date().toISOString().split('T')[0];
  const overdue = followUps.filter(f => f.status === 'pending' && f.due_date < today);
  const dueToday = followUps.filter(f => f.status === 'pending' && f.due_date === today);
  const upcoming = followUps.filter(f => f.status === 'pending' && f.due_date > today);
  const completed = followUps.filter(f => f.status === 'completed');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Follow-ups</h1>
        <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-1" /> Add</Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <>
          <FollowUpSection title="Overdue" items={overdue} variant="destructive" onComplete={handleComplete} onSnooze={setSnoozeId} onEdit={setEditFollowUp} />
          <FollowUpSection title="Due Today" items={dueToday} variant="default" onComplete={handleComplete} onSnooze={setSnoozeId} onEdit={setEditFollowUp} />
          <FollowUpSection title="Upcoming" items={upcoming} variant="secondary" onComplete={handleComplete} onSnooze={setSnoozeId} onEdit={setEditFollowUp} />
          <FollowUpSection title="Completed" items={completed.slice(0, 10)} variant="outline" onComplete={handleComplete} onSnooze={setSnoozeId} hideActions />
        </>
      )}

      <FollowUpFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} contacts={contacts} />

      {editFollowUp && (
        <FollowUpFormDialog
          open={true}
          onOpenChange={() => setEditFollowUp(null)}
          onSaved={load}
          contacts={contacts}
          followUp={editFollowUp}
        />
      )}

      <SnoozeDialog
        open={!!snoozeId}
        onOpenChange={() => setSnoozeId(null)}
        snoozeDate={snoozeDate}
        onSnoozeDateChange={setSnoozeDate}
        onConfirm={handleSnooze}
      />
    </div>
  );
}

function FollowUpFormDialog({ open, onOpenChange, onSaved, contacts, followUp }: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSaved: () => void;
  contacts: Contact[];
  followUp?: FollowUp;
}) {
  const isEdit = !!followUp;
  const [form, setForm] = useState({ contact_id: '', title: '', due_date: '', due_time: '', notes: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (followUp) {
      setForm({
        contact_id: followUp.contact_id || '',
        title: followUp.title || '',
        due_date: followUp.due_date || '',
        due_time: followUp.due_time || '',
        notes: followUp.notes || '',
      });
    } else {
      setForm({ contact_id: '', title: '', due_date: '', due_time: '', notes: '' });
    }
  }, [followUp]);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      if (isEdit) {
        await updateFollowUp(followUp.id, form);
      } else {
        await createFollowUp(form);
      }
      onOpenChange(false);
      setForm({ contact_id: '', title: '', due_date: '', due_time: '', notes: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>{isEdit ? 'Edit Follow-up' : 'New Follow-up'}</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Send proposal, Follow up on meeting" /></div>
          <div className="space-y-2">
            <Label>Contact *</Label>
            <Select value={form.contact_id} onValueChange={v => setForm(f => ({ ...f, contact_id: v === '_none' ? '' : v }))}>
              <SelectTrigger><SelectValue placeholder="Select contact" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="_none">None</SelectItem>
                {contacts.map(c => <SelectItem key={c.id} value={c.id}>{c.first_name} {c.last_name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Due Date *</Label><Input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Due Time</Label><Input type="time" value={form.due_time} onChange={e => setForm(f => ({ ...f, due_time: e.target.value }))} /></div>
          </div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.title || !form.due_date || !form.contact_id}>{isEdit ? 'Update' : 'Save'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
