import { useEffect, useState } from 'react';
import { getDeals, getContacts, getCompanies } from '@/api';
import type { Deal, Contact, Company } from '@/types';
import { DEAL_STAGES } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { formatCurrency } from '@/constants';
import { DealFormDialog } from '@/components/shared/DealFormDialog';

const stageColumnColors: Record<string, string> = {
  lead: 'border-t-gray-400',
  prospect: 'border-t-blue-400',
  qualified: 'border-t-indigo-400',
  proposal: 'border-t-purple-400',
  negotiation: 'border-t-orange-400',
  won: 'border-t-green-400',
  lost: 'border-t-red-400',
};

export function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editDeal, setEditDeal] = useState<Deal | null>(null);

  const load = () => {
    Promise.all([getDeals(), getContacts(), getCompanies()])
      .then(([d, c, co]) => {
        setDeals(d.data);
        setContacts(c.data);
        setCompanies(co.data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const contactMap = Object.fromEntries(contacts.map(c => [c.id, `${c.first_name} ${c.last_name}`.trim()]));
  const companyMap = Object.fromEntries(companies.map(c => [c.id, c.name]));

  const dealsByStage = (stage: string) => deals.filter(d => d.stage === stage);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Deals</h1>
        <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-1" /> Add</Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : deals.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No deals yet</div>
      ) : (
        <>
          {/* Desktop: horizontal columns */}
          <div className="hidden md:flex gap-3 overflow-x-auto pb-4">
            {DEAL_STAGES.map(stage => {
              const stageDeals = dealsByStage(stage);
              const stageTotal = stageDeals.reduce((sum, d) => sum + Number(d.value || 0), 0);
              return (
                <div key={stage} className="flex-shrink-0 w-56">
                  <div className={`border-t-4 ${stageColumnColors[stage] || 'border-t-gray-400'} rounded-t bg-muted/50 px-3 py-2`}>
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-sm capitalize">{stage}</span>
                      <Badge variant="secondary" className="text-xs">{stageDeals.length}</Badge>
                    </div>
                    {stageTotal > 0 && (
                      <p className="text-xs text-muted-foreground mt-0.5">{formatCurrency(stageTotal)}</p>
                    )}
                  </div>
                  <div className="min-h-[120px] space-y-2 p-2 bg-muted/20 rounded-b">
                    {stageDeals.map(d => (
                      <Card key={d.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setEditDeal(d)}>
                        <CardContent className="p-3">
                          <p className="font-medium text-sm">{d.title}</p>
                          {(contactMap[d.contact_id] || companyMap[d.company_id]) && (
                            <p className="text-xs text-muted-foreground mt-0.5 truncate">
                              {[contactMap[d.contact_id], companyMap[d.company_id]].filter(Boolean).join(' - ')}
                            </p>
                          )}
                          <p className="text-sm text-muted-foreground mt-1">{formatCurrency(d.value, d.currency)}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant={d.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs">{d.priority}</Badge>
                            {d.expected_close && <span className="text-xs text-muted-foreground">Close: {d.expected_close}</span>}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Mobile: stacked sections */}
          <div className="md:hidden space-y-4">
            {DEAL_STAGES.map(stage => {
              const stageDeals = dealsByStage(stage);
              if (stageDeals.length === 0) return null;
              return (
                <div key={stage} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-sm capitalize">{stage}</h2>
                    <Badge variant="secondary" className="text-xs">{stageDeals.length}</Badge>
                  </div>
                  {stageDeals.map(d => (
                    <Card key={d.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setEditDeal(d)}>
                      <CardContent className="p-3 flex justify-between items-center">
                        <div>
                          <p className="font-medium text-sm">{d.title}</p>
                          {(contactMap[d.contact_id] || companyMap[d.company_id]) && (
                            <p className="text-xs text-muted-foreground truncate">
                              {[contactMap[d.contact_id], companyMap[d.company_id]].filter(Boolean).join(' - ')}
                            </p>
                          )}
                          <p className="text-sm text-muted-foreground">{formatCurrency(d.value, d.currency)}</p>
                        </div>
                        <Badge variant={d.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs">{d.priority}</Badge>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              );
            })}
          </div>
        </>
      )}

      <DealFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} contacts={contacts} companies={companies} />
      {editDeal && (
        <DealFormDialog open={true} onOpenChange={() => setEditDeal(null)} onSaved={load} deal={editDeal} contacts={contacts} companies={companies} />
      )}
    </div>
  );
}
