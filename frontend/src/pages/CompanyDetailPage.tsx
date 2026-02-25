import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCompany, updateCompany } from '@/api';
import type { Company, Contact } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft, Edit, Save, X, Mail, Phone } from 'lucide-react';

export function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [company, setCompany] = useState<(Company & { contacts: Contact[] }) | null>(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Company>>({});

  useEffect(() => {
    if (id) getCompany(id).then(res => { setCompany(res.data); setEditForm(res.data); });
  }, [id]);

  const handleSave = async () => {
    if (!id) return;
    await updateCompany(id, editForm);
    const res = await getCompany(id);
    setCompany(res.data);
    setEditing(false);
  };

  if (!company) return <div className="py-8 text-center">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/companies')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">{company.name}</h1>
        <div className="ml-auto flex gap-2">
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

      <Card>
        <CardHeader><CardTitle>Company Details</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {editing ? (
            <>
              <div className="space-y-2"><Label>Name</Label><Input value={editForm.name || ''} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Industry</Label><Input value={editForm.industry || ''} onChange={e => setEditForm(f => ({ ...f, industry: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Website</Label><Input value={editForm.website || ''} onChange={e => setEditForm(f => ({ ...f, website: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Size</Label><Input value={editForm.size || ''} onChange={e => setEditForm(f => ({ ...f, size: e.target.value }))} /></div>
              <div className="space-y-2 col-span-2"><Label>Notes</Label><Textarea value={editForm.notes || ''} onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))} /></div>
            </>
          ) : (
            <>
              {company.industry && <div><p className="text-sm text-muted-foreground">Industry</p><p>{company.industry}</p></div>}
              {company.website && <div><p className="text-sm text-muted-foreground">Website</p><a href={company.website} target="_blank" rel="noopener noreferrer" className="text-primary">{company.website}</a></div>}
              {company.size && <div><p className="text-sm text-muted-foreground">Size</p><p>{company.size}</p></div>}
              {company.notes && <div className="col-span-2"><p className="text-sm text-muted-foreground">Notes</p><p>{company.notes}</p></div>}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Contacts ({company.contacts?.length || 0})</CardTitle></CardHeader>
        <CardContent>
          {company.contacts?.length ? (
            <div className="space-y-2">
              {company.contacts.map(c => (
                <div key={c.id} className="flex items-center justify-between p-3 rounded border cursor-pointer hover:bg-accent" onClick={() => navigate(`/contacts/${c.id}`)}>
                  <div>
                    <p className="font-medium">{c.first_name} {c.last_name}</p>
                    <p className="text-sm text-muted-foreground">{c.role}</p>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    {c.email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{c.email}</span>}
                    {c.phone && <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{c.phone}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No contacts at this company</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
