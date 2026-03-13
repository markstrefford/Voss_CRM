import { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { getDeals, updateDealStage, getContacts, getCompanies } from '@/api';
import type { Deal, DealStage, Contact, Company } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { formatCurrency } from '@/constants';
import { DealFormDialog } from '@/components/shared/DealFormDialog';

const PIPELINE_STAGES: DealStage[] = ['lead', 'prospect', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];

const stageColors: Record<string, string> = {
  lead: 'border-t-gray-400',
  prospect: 'border-t-blue-400',
  qualified: 'border-t-indigo-400',
  proposal: 'border-t-purple-400',
  negotiation: 'border-t-orange-400',
  won: 'border-t-green-400',
  lost: 'border-t-red-400',
};

export function PipelinePage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set(PIPELINE_STAGES));
  const [showForm, setShowForm] = useState(false);
  const [editDeal, setEditDeal] = useState<Deal | null>(null);
  const [createStage, setCreateStage] = useState<DealStage | undefined>(undefined);

  const load = () => {
    Promise.all([getDeals(), getContacts(), getCompanies()])
      .then(([d, c, co]) => { setDeals(d.data); setContacts(c.data); setCompanies(co.data); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const contactMap = Object.fromEntries(contacts.map(c => [c.id, `${c.first_name} ${c.last_name}`.trim()]));
  const companyMap = Object.fromEntries(companies.map(c => [c.id, c.name]));

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;
    const dealId = result.draggableId;
    const newStage = result.destination.droppableId as DealStage;

    setDeals(prev => prev.map(d => d.id === dealId ? { ...d, stage: newStage } : d));
    try {
      await updateDealStage(dealId, newStage);
    } catch {
      getDeals().then(res => setDeals(res.data));
    }
  };

  const toggleStage = (stage: string) => {
    setExpandedStages(prev => {
      const next = new Set(prev);
      if (next.has(stage)) next.delete(stage);
      else next.add(stage);
      return next;
    });
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;

  const dealsByStage = (stage: string) => deals.filter(d => d.stage === stage);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pipeline</h1>
        <Button onClick={() => { setCreateStage(undefined); setShowForm(true); }}><Plus className="h-4 w-4 mr-1" /> Add Deal</Button>
      </div>

      <DragDropContext onDragEnd={handleDragEnd}>
        {/* Desktop: horizontal columns */}
        <div className="hidden md:flex gap-3 overflow-x-auto pb-4">
          {PIPELINE_STAGES.map(stage => {
            const stageDeals = dealsByStage(stage);
            const stageTotal = stageDeals.reduce((sum, d) => sum + Number(d.value || 0), 0);
            return (
              <div key={stage} className="flex-shrink-0 w-56">
                <div className={`border-t-4 ${stageColors[stage]} rounded-t bg-muted/50 px-3 py-2`}>
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-sm capitalize">{stage}</span>
                    <Badge variant="secondary" className="text-xs">{stageDeals.length}</Badge>
                  </div>
                  {stageTotal > 0 && (
                    <p className="text-xs text-muted-foreground mt-0.5">{formatCurrency(stageTotal)}</p>
                  )}
                </div>
                <Droppable droppableId={stage}>
                  {(provided) => (
                    <div ref={provided.innerRef} {...provided.droppableProps} className="min-h-[200px] space-y-2 p-2 bg-muted/20 rounded-b">
                      {stageDeals.map((deal, index) => (
                        <Draggable key={deal.id} draggableId={deal.id} index={index}>
                          {(provided) => (
                            <Card
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className="cursor-pointer hover:shadow-md transition-shadow"
                              onClick={() => setEditDeal(deal)}
                            >
                              <CardContent className="p-3">
                                <p className="font-medium text-sm">{deal.title}</p>
                                {(contactMap[deal.contact_id] || companyMap[deal.company_id]) && (
                                  <p className="text-xs text-muted-foreground mt-0.5 truncate">
                                    {[contactMap[deal.contact_id], companyMap[deal.company_id]].filter(Boolean).join(' - ')}
                                  </p>
                                )}
                                <p className="text-sm text-muted-foreground mt-1">{formatCurrency(deal.value, deal.currency)}</p>
                                <div className="flex items-center gap-2 mt-2">
                                  <Badge variant={deal.priority === 'high' ? 'destructive' : 'secondary'} className="mt-2 text-xs">
                                    {deal.priority}
                                  </Badge>
                                  {deal.expected_close && <span className="text-xs text-muted-foreground">Close: {deal.expected_close}</span>}
                                </div>
                              </CardContent>
                            </Card>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            );
          })}
        </div>

        {/* Mobile: collapsible sections */}
        <div className="md:hidden space-y-2">
          {PIPELINE_STAGES.map(stage => {
            const stageDeals = dealsByStage(stage);
            const stageTotal = stageDeals.reduce((sum, d) => sum + Number(d.value || 0), 0);
            return (
              <div key={stage}>
                <button
                  className={`w-full border-t-4 ${stageColors[stage]} rounded-t bg-muted/50 px-3 py-2 flex justify-between items-center`}
                  onClick={() => toggleStage(stage)}
                >
                  <div className="text-left">
                    <span className="font-medium text-sm capitalize">{stage}</span>
                    {stageTotal > 0 && (
                      <p className="text-xs text-muted-foreground">{formatCurrency(stageTotal)}</p>
                    )}
                  </div>
                  <Badge variant="secondary" className="text-xs">{stageDeals.length}</Badge>
                </button>
                {expandedStages.has(stage) && (
                  <Droppable droppableId={stage}>
                    {(provided) => (
                      <div ref={provided.innerRef} {...provided.droppableProps} className="space-y-2 p-2 bg-muted/20 rounded-b">
                        {stageDeals.map((deal, index) => (
                          <Draggable key={deal.id} draggableId={deal.id} index={index}>
                            {(provided) => (
                              <Card
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className="cursor-pointer hover:shadow-md transition-shadow"
                                onClick={() => setEditDeal(deal)}
                              >
                                <CardContent className="p-3 flex justify-between items-center">
                                  <div>
                                    <p className="font-medium text-sm">{deal.title}</p>
                                    {(contactMap[deal.contact_id] || companyMap[deal.company_id]) && (
                                      <p className="text-xs text-muted-foreground truncate">
                                        {[contactMap[deal.contact_id], companyMap[deal.company_id]].filter(Boolean).join(' - ')}
                                      </p>
                                    )}
                                    <p className="text-sm text-muted-foreground">{formatCurrency(deal.value, deal.currency)}</p>
                                  </div>
                                  <Badge variant={deal.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs">{deal.priority}</Badge>
                                </CardContent>
                              </Card>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                )}
              </div>
            );
          })}
        </div>
      </DragDropContext>

      <DealFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} contacts={contacts} companies={companies} defaultStage={createStage} />
      {editDeal && (
        <DealFormDialog open={true} onOpenChange={() => setEditDeal(null)} onSaved={load} deal={editDeal} contacts={contacts} companies={companies} />
      )}
    </div>
  );
}
