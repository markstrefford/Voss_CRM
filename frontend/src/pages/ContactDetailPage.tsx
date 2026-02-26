import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getContact, updateContact, getInteractions, createInteraction, getDeals, getFollowUps, createFollowUp, completeFollowUp, snoozeFollowUp } from '@/api';
import type { Contact, Interaction, Deal, FollowUp } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TagInput } from '@/components/shared/TagInput';
import { EmailDraftModal } from '@/components/email/EmailDraftModal';
import { ArrowLeft, Edit, Save, X, Plus, Mail, Check, Clock, CalendarPlus, ChevronDown, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';

const SEGMENTS = ['', 'signal_strata', 'consulting', 'pe', 'other'] as const;
const ENGAGEMENT_STAGES = ['new', 'nurturing', 'active', 'client', 'churned'] as const;
const INBOUND_CHANNELS = ['', 'linkedin', 'referral', 'conference', 'cold_outbound', 'website', 'other'] as const;

export function ContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contact, setContact] = useState<Contact | null>(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Contact>>({});
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [showInteractionForm, setShowInteractionForm] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);
  const [snoozeId, setSnoozeId] = useState<string | null>(null);
  const [snoozeDate, setSnoozeDate] = useState('');
  const [showCompleted, setShowCompleted] = useState(false);

  useEffect(() => {
    if (!id) return;
    getContact(id).then(res => { setContact(res.data); setEditForm(res.data); });
    getInteractions({ contact_id: id }).then(res => setInteractions(res.data));
    getDeals({ contact_id: id }).then(res => setDeals(res.data));
    loadFollowUps(id);
  }, [id]);

  const loadFollowUps = (contactId: string) => {
    getFollowUps({ contact_id: contactId }).then(res => setFollowUps(res.data));
  };

  const handleCompleteFollowUp = async (followUpId: string) => {
    await completeFollowUp(followUpId);
    if (id) loadFollowUps(id);
  };

  const handleSnooze = async () => {
    if (snoozeId && snoozeDate) {
      await snoozeFollowUp(snoozeId, snoozeDate);
      setSnoozeId(null);
      setSnoozeDate('');
      if (id) loadFollowUps(id);
    }
  };

  const pendingFollowUps = followUps.filter(f => f.status === 'pending');
  const today = new Date().toISOString().split('T')[0];
  const overdueFollowUps = followUps.filter(f => f.status === 'pending' && f.due_date < today);
  const dueTodayFollowUps = followUps.filter(f => f.status === 'pending' && f.due_date === today);
  const upcomingFollowUps = followUps.filter(f => f.status === 'pending' && f.due_date > today);
  const completedFollowUps = followUps.filter(f => f.status === 'completed');

  const handleSave = async () => {
    if (!id) return;
    const res = await updateContact(id, editForm);
    setContact(res.data);
    setEditing(false);
  };

  if (!contact) return <div className="py-8 text-center">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/contacts')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">{contact.first_name} {contact.last_name}</h1>
        <div className="ml-auto flex gap-2">
          <Button variant="outline" onClick={() => setShowEmailModal(true)}>
            <Mail className="h-4 w-4 mr-1" /> Draft Email
          </Button>
          {editing ? (
            <>
              <Button variant="ghost" onClick={() => setEditing(false)}><X className="h-4 w-4" /></Button>
              <Button onClick={handleSave}><Save className="h-4 w-4 mr-1" /> Save</Button>
            </>
          ) : (
            <Button variant="outline" onClick={() => setEditing(true)}><Edit className="h-4 w-4 mr-1" /> Edit</Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="info">
        <TabsList>
          <TabsTrigger value="info">Info</TabsTrigger>
          <TabsTrigger value="timeline">Timeline ({interactions.length})</TabsTrigger>
          <TabsTrigger value="deals">Deals ({deals.length})</TabsTrigger>
          <TabsTrigger value="followups">Follow-ups ({pendingFollowUps.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              {editing ? (
                <>
                  <div className="space-y-2"><Label>First Name</Label><Input value={editForm.first_name || ''} onChange={e => setEditForm(f => ({ ...f, first_name: e.target.value }))} /></div>
                  <div className="space-y-2"><Label>Last Name</Label><Input value={editForm.last_name || ''} onChange={e => setEditForm(f => ({ ...f, last_name: e.target.value }))} /></div>
                  <div className="space-y-2"><Label>Email</Label><Input value={editForm.email || ''} onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))} /></div>
                  <div className="space-y-2"><Label>Phone</Label><Input value={editForm.phone || ''} onChange={e => setEditForm(f => ({ ...f, phone: e.target.value }))} /></div>
                  <div className="space-y-2"><Label>Role</Label><Input value={editForm.role || ''} onChange={e => setEditForm(f => ({ ...f, role: e.target.value }))} /></div>
                  <div className="space-y-2"><Label>LinkedIn</Label><Input value={editForm.linkedin_url || ''} onChange={e => setEditForm(f => ({ ...f, linkedin_url: e.target.value }))} /></div>
                  <div className="space-y-2">
                    <Label>Segment</Label>
                    <Select value={editForm.segment || ''} onValueChange={v => setEditForm(f => ({ ...f, segment: v }))}>
                      <SelectTrigger><SelectValue placeholder="Select segment" /></SelectTrigger>
                      <SelectContent>
                        {SEGMENTS.filter(Boolean).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Engagement Stage</Label>
                    <Select value={editForm.engagement_stage || ''} onValueChange={v => setEditForm(f => ({ ...f, engagement_stage: v }))}>
                      <SelectTrigger><SelectValue placeholder="Select stage" /></SelectTrigger>
                      <SelectContent>
                        {ENGAGEMENT_STAGES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Inbound Channel</Label>
                    <Select value={editForm.inbound_channel || ''} onValueChange={v => setEditForm(f => ({ ...f, inbound_channel: v }))}>
                      <SelectTrigger><SelectValue placeholder="Select channel" /></SelectTrigger>
                      <SelectContent>
                        {INBOUND_CHANNELS.filter(Boolean).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2 col-span-2"><Label>Tags</Label><TagInput value={editForm.tags || ''} onChange={v => setEditForm(f => ({ ...f, tags: v }))} /></div>
                  <div className="space-y-2 col-span-2"><Label>Notes</Label><Textarea value={editForm.notes || ''} onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))} /></div>
                </>
              ) : (
                <>
                  <InfoRow label="Email" value={contact.email} />
                  <InfoRow label="Phone" value={contact.phone} />
                  <InfoRow label="Role" value={contact.role} />
                  <InfoRow label="LinkedIn" value={contact.linkedin_url} link />
                  <InfoRow label="Source" value={contact.source} />
                  <InfoRow label="Status" value={contact.status} />
                  <InfoRow label="Segment" value={contact.segment} />
                  <InfoRow label="Engagement Stage" value={contact.engagement_stage} />
                  <InfoRow label="Inbound Channel" value={contact.inbound_channel} />
                  <div className="col-span-2">
                    <p className="text-sm text-muted-foreground">Tags</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {contact.tags ? contact.tags.split(',').map(t => <Badge key={t.trim()} variant="secondary">{t.trim()}</Badge>) : <span className="text-muted-foreground text-sm">None</span>}
                    </div>
                  </div>
                  {contact.notes && <div className="col-span-2"><p className="text-sm text-muted-foreground">Notes</p><p className="mt-1">{contact.notes}</p></div>}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline">
          <div className="space-y-4">
            <Button onClick={() => setShowInteractionForm(true)}><Plus className="h-4 w-4 mr-1" /> Log Interaction</Button>
            {interactions.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">No interactions yet</p>
            ) : (
              interactions.map(i => (
                <Card key={i.id}>
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{i.type}</Badge>
                          <Badge variant="secondary">{i.direction}</Badge>
                        </div>
                        {i.subject && <p className="font-medium mt-1">{i.subject}</p>}
                        {i.body && <p className="text-sm text-muted-foreground mt-1">{i.body}</p>}
                        {i.url && <a href={i.url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary mt-1 block">{i.url}</a>}
                      </div>
                      <span className="text-xs text-muted-foreground">{i.occurred_at ? format(new Date(i.occurred_at), 'MMM d, yyyy') : ''}</span>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <InteractionFormDialog open={showInteractionForm} onOpenChange={setShowInteractionForm} contactId={id!} onSaved={() => getInteractions({ contact_id: id! }).then(res => setInteractions(res.data))} />
        </TabsContent>

        <TabsContent value="deals">
          {deals.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">No deals</p>
          ) : (
            <div className="space-y-2">
              {deals.map(d => (
                <Card key={d.id} className="cursor-pointer" onClick={() => navigate(`/deals`)}>
                  <CardContent className="pt-4 flex justify-between items-center">
                    <div>
                      <p className="font-medium">{d.title}</p>
                      <p className="text-sm text-muted-foreground">${Number(d.value || 0).toLocaleString()} {d.currency}</p>
                    </div>
                    <Badge>{d.stage}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="followups">
          <div className="space-y-4">
            <Button onClick={() => setShowFollowUpForm(true)}><Plus className="h-4 w-4 mr-1" /> Schedule Follow-up</Button>

            {followUps.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">No follow-ups</p>
            ) : (
              <>
                <FollowUpSection title="Overdue" items={overdueFollowUps} variant="destructive" onComplete={handleCompleteFollowUp} onSnooze={setSnoozeId} />
                <FollowUpSection title="Due Today" items={dueTodayFollowUps} variant="default" onComplete={handleCompleteFollowUp} onSnooze={setSnoozeId} />
                <FollowUpSection title="Upcoming" items={upcomingFollowUps} variant="secondary" onComplete={handleCompleteFollowUp} onSnooze={setSnoozeId} />
                {completedFollowUps.length > 0 && (
                  <div className="space-y-2">
                    <button
                      className="text-lg font-semibold flex items-center gap-2 hover:opacity-80"
                      onClick={() => setShowCompleted(v => !v)}
                    >
                      {showCompleted ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      Completed <Badge variant="outline">{completedFollowUps.length}</Badge>
                    </button>
                    {showCompleted && (
                      <div className="space-y-2">
                        {completedFollowUps.slice(0, 5).map(f => (
                          <Card key={f.id}>
                            <CardContent className="pt-4">
                              <p className="font-medium line-through text-muted-foreground">{f.title}</p>
                              <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                <Clock className="h-3 w-3" />
                                {f.due_date} {f.due_time && `at ${f.due_time}`}
                              </div>
                              {f.notes && <p className="text-sm text-muted-foreground mt-1">{f.notes}</p>}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          <FollowUpFormDialog
            open={showFollowUpForm}
            onOpenChange={setShowFollowUpForm}
            contactId={id!}
            onSaved={() => loadFollowUps(id!)}
          />

          <Dialog open={!!snoozeId} onOpenChange={() => setSnoozeId(null)}>
            <DialogContent>
              <DialogHeader><DialogTitle>Snooze Follow-up</DialogTitle></DialogHeader>
              <div className="space-y-2">
                <Label>New Due Date</Label>
                <Input type="date" value={snoozeDate} onChange={e => setSnoozeDate(e.target.value)} />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setSnoozeId(null)}>Cancel</Button>
                <Button onClick={handleSnooze} disabled={!snoozeDate}>Snooze</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>
      </Tabs>

      {showEmailModal && <EmailDraftModal open={showEmailModal} onOpenChange={setShowEmailModal} contactId={id!} />}
    </div>
  );
}

function InfoRow({ label, value, link }: { label: string; value: string; link?: boolean }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      {link ? <a href={value} target="_blank" rel="noopener noreferrer" className="text-primary">{value}</a> : <p>{value}</p>}
    </div>
  );
}

function InteractionFormDialog({ open, onOpenChange, contactId, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; contactId: string; onSaved: () => void }) {
  const [form, setForm] = useState({ type: 'note', subject: '', body: '', url: '', direction: 'outbound' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createInteraction({ ...form, contact_id: contactId });
      onOpenChange(false);
      setForm({ type: 'note', subject: '', body: '', url: '', direction: 'outbound' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Log Interaction</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={form.type} onValueChange={v => setForm(f => ({ ...f, type: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {['call', 'email', 'meeting', 'note', 'linkedin_message', 'other'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Direction</Label>
              <Select value={form.direction} onValueChange={v => setForm(f => ({ ...f, direction: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {['inbound', 'outbound', 'internal'].map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2"><Label>Subject</Label><Input value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Details</Label><Textarea value={form.body} onChange={e => setForm(f => ({ ...f, body: e.target.value }))} /></div>
          <div className="space-y-2"><Label>URL (optional)</Label><Input value={form.url} onChange={e => setForm(f => ({ ...f, url: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function FollowUpSection({ title, items, variant, onComplete, onSnooze }: {
  title: string;
  items: FollowUp[];
  variant: 'default' | 'destructive' | 'secondary' | 'outline';
  onComplete: (id: string) => void;
  onSnooze: (id: string) => void;
}) {
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
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" title="Complete" onClick={() => onComplete(f.id)}>
                  <Check className="h-4 w-4 text-green-600" />
                </Button>
                <Button variant="ghost" size="icon" title="Snooze" onClick={() => onSnooze(f.id)}>
                  <CalendarPlus className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function FollowUpFormDialog({ open, onOpenChange, contactId, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; contactId: string; onSaved: () => void }) {
  const [form, setForm] = useState({ title: '', due_date: '', due_time: '', notes: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createFollowUp({ ...form, contact_id: contactId });
      onOpenChange(false);
      setForm({ title: '', due_date: '', due_time: '', notes: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>Schedule Follow-up</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Send proposal, Follow up on meeting" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Due Date *</Label><Input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Due Time</Label><Input type="time" value={form.due_time} onChange={e => setForm(f => ({ ...f, due_time: e.target.value }))} /></div>
          </div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.title || !form.due_date}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
