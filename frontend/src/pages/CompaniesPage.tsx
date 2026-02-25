import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCompanies, createCompany } from '@/api';
import type { Company } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Globe, Building2 } from 'lucide-react';

export function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const navigate = useNavigate();

  const load = () => {
    getCompanies().then(res => setCompanies(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Companies</h1>
        <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-1" /> Add</Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : companies.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No companies yet</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {companies.map(c => (
            <Card key={c.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/companies/${c.id}`)}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                  <p className="font-semibold">{c.name}</p>
                </div>
                {c.industry && <p className="text-sm text-muted-foreground mt-1">{c.industry}</p>}
                {c.website && (
                  <div className="flex items-center gap-1 text-sm mt-1">
                    <Globe className="h-3 w-3" />
                    <span className="text-primary truncate">{c.website}</span>
                  </div>
                )}
                {c.size && <p className="text-sm text-muted-foreground mt-1">{c.size} employees</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CompanyFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} />
    </div>
  );
}

function CompanyFormDialog({ open, onOpenChange, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: '', industry: '', website: '', size: '', notes: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createCompany(form);
      onOpenChange(false);
      setForm({ name: '', industry: '', website: '', size: '', notes: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Company</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Name *</Label><Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Industry</Label><Input value={form.industry} onChange={e => setForm(f => ({ ...f, industry: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Size</Label><Input value={form.size} onChange={e => setForm(f => ({ ...f, size: e.target.value }))} /></div>
          </div>
          <div className="space-y-2"><Label>Website</Label><Input value={form.website} onChange={e => setForm(f => ({ ...f, website: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.name}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
