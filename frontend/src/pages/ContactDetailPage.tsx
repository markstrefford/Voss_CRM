import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getContact, updateContact, getInteractions, createInteraction, getDeals } from '@/api';
import type { Contact, Interaction, Deal } from '@/types';
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
import { ArrowLeft, Edit, Save, X, Plus, Mail } from 'lucide-react';
import { format } from 'date-fns';

export function ContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contact, setContact] = useState<Contact | null>(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Contact>>({});
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [showInteractionForm, setShowInteractionForm] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);

  useEffect(() => {
    if (!id) return;
    getContact(id).then(res => { setContact(res.data); setEditForm(res.data); });
    getInteractions({ contact_id: id }).then(res => setInteractions(res.data));
    getDeals({ contact_id: id }).then(res => setDeals(res.data));
  }, [id]);

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
