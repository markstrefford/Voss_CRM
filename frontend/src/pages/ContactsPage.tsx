import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getContacts, createContact, deleteContact } from '@/api';
import type { Contact } from '@/types';
import { useDebounce } from '@/hooks/useDebounce';
import { SearchBar } from '@/components/shared/SearchBar';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Trash2, Mail, Phone } from 'lucide-react';
import { SEGMENTS, ENGAGEMENT_STAGES, INBOUND_CHANNELS } from '@/constants';

export function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const debouncedSearch = useDebounce(search, 300);
  const navigate = useNavigate();

  const load = () => {
    const params: Record<string, string> = {};
    if (debouncedSearch) params.q = debouncedSearch;
    getContacts(params)
      .then(res => setContacts(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [debouncedSearch]);

  const handleDelete = () => {
    if (deleteId) {
      deleteContact(deleteId).then(load);
      setDeleteId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Contacts</h1>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4 mr-1" /> Add
        </Button>
      </div>

      <SearchBar value={search} onChange={setSearch} placeholder="Search contacts..." />

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : contacts.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No contacts found</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contacts.map(c => (
            <Card key={c.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/contacts/${c.id}`)}>
              <CardContent className="pt-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold">{c.first_name} {c.last_name}</p>
                    <p className="text-sm text-muted-foreground">{c.role}</p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={e => { e.stopPropagation(); setDeleteId(c.id); }}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="mt-2 space-y-1 text-sm">
                  {c.email && <div className="flex items-center gap-1"><Mail className="h-3 w-3" />{c.email}</div>}
                  {c.phone && <div className="flex items-center gap-1"><Phone className="h-3 w-3" />{c.phone}</div>}
                </div>
                {(c.segment || c.engagement_stage) && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {c.segment && <Badge variant="outline" className="text-xs">{c.segment}</Badge>}
                    {c.engagement_stage && <Badge variant="secondary" className="text-xs">{c.engagement_stage}</Badge>}
                  </div>
                )}
                {c.tags && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {c.tags.split(',').map(t => <Badge key={t.trim()} variant="secondary" className="text-xs">{t.trim()}</Badge>)}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ContactFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} />
      <ConfirmDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)} title="Delete Contact" description="This will archive the contact." onConfirm={handleDelete} variant="destructive" />
    </div>
  );
}

function ContactFormDialog({ open, onOpenChange, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; onSaved: () => void }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', role: '', tags: '', notes: '', segment: '', engagement_stage: 'new', inbound_channel: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createContact(form);
      onOpenChange(false);
      setForm({ first_name: '', last_name: '', email: '', phone: '', role: '', tags: '', notes: '', segment: '', engagement_stage: 'new', inbound_channel: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Contact</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2"><Label>First Name *</Label><Input value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Last Name</Label><Input value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Email</Label><Input value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Phone</Label><Input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} /></div>
          <div className="space-y-2 col-span-2"><Label>Role</Label><Input value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} /></div>
          <div className="space-y-2">
            <Label>Segment</Label>
            <Select value={form.segment} onValueChange={v => setForm(f => ({ ...f, segment: v }))}>
              <SelectTrigger><SelectValue placeholder="Select segment" /></SelectTrigger>
              <SelectContent>
                {SEGMENTS.filter(Boolean).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Engagement Stage</Label>
            <Select value={form.engagement_stage} onValueChange={v => setForm(f => ({ ...f, engagement_stage: v }))}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {ENGAGEMENT_STAGES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 col-span-2">
            <Label>Inbound Channel</Label>
            <Select value={form.inbound_channel} onValueChange={v => setForm(f => ({ ...f, inbound_channel: v }))}>
              <SelectTrigger><SelectValue placeholder="Select channel" /></SelectTrigger>
              <SelectContent>
                {INBOUND_CHANNELS.filter(Boolean).map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 col-span-2"><Label>Tags (comma-separated)</Label><Input value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} /></div>
          <div className="space-y-2 col-span-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.first_name}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
