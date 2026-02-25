import { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { getDeals, updateDealStage } from '@/api';
import type { Deal, DealStage } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DollarSign } from 'lucide-react';

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
  const [loading, setLoading] = useState(true);
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set(PIPELINE_STAGES));

  useEffect(() => {
    getDeals().then(res => setDeals(res.data)).finally(() => setLoading(false));
  }, []);

  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;
    const dealId = result.draggableId;
    const newStage = result.destination.droppableId as DealStage;

    setDeals(prev => prev.map(d => d.id === dealId ? { ...d, stage: newStage } : d));
    try {
      await updateDealStage(dealId, newStage);
    } catch {
      // Revert on error
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
      <h1 className="text-2xl font-bold">Pipeline</h1>

      <DragDropContext onDragEnd={handleDragEnd}>
        {/* Desktop: horizontal columns */}
        <div className="hidden md:flex gap-3 overflow-x-auto pb-4">
          {PIPELINE_STAGES.map(stage => (
            <div key={stage} className="flex-shrink-0 w-56">
              <div className={`border-t-4 ${stageColors[stage]} rounded-t bg-muted/50 px-3 py-2 flex justify-between items-center`}>
                <span className="font-medium text-sm capitalize">{stage}</span>
                <Badge variant="secondary" className="text-xs">{dealsByStage(stage).length}</Badge>
              </div>
              <Droppable droppableId={stage}>
                {(provided) => (
                  <div ref={provided.innerRef} {...provided.droppableProps} className="min-h-[200px] space-y-2 p-2 bg-muted/20 rounded-b">
                    {dealsByStage(stage).map((deal, index) => (
                      <Draggable key={deal.id} draggableId={deal.id} index={index}>
                        {(provided) => (
                          <Card ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} className="cursor-grab active:cursor-grabbing">
                            <CardContent className="p-3">
                              <p className="font-medium text-sm">{deal.title}</p>
                              <div className="flex items-center gap-1 mt-1 text-sm text-muted-foreground">
                                <DollarSign className="h-3 w-3" />
                                {Number(deal.value || 0).toLocaleString()}
                              </div>
                              <Badge variant={deal.priority === 'high' ? 'destructive' : 'secondary'} className="mt-2 text-xs">
                                {deal.priority}
                              </Badge>
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
          ))}
        </div>

        {/* Mobile: collapsible sections */}
        <div className="md:hidden space-y-2">
          {PIPELINE_STAGES.map(stage => (
            <div key={stage}>
              <button
                className={`w-full border-t-4 ${stageColors[stage]} rounded-t bg-muted/50 px-3 py-2 flex justify-between items-center`}
                onClick={() => toggleStage(stage)}
              >
                <span className="font-medium text-sm capitalize">{stage}</span>
                <Badge variant="secondary" className="text-xs">{dealsByStage(stage).length}</Badge>
              </button>
              {expandedStages.has(stage) && (
                <Droppable droppableId={stage}>
                  {(provided) => (
                    <div ref={provided.innerRef} {...provided.droppableProps} className="space-y-2 p-2 bg-muted/20 rounded-b">
                      {dealsByStage(stage).map((deal, index) => (
                        <Draggable key={deal.id} draggableId={deal.id} index={index}>
                          {(provided) => (
                            <Card ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}>
                              <CardContent className="p-3 flex justify-between items-center">
                                <div>
                                  <p className="font-medium text-sm">{deal.title}</p>
                                  <p className="text-sm text-muted-foreground">${Number(deal.value || 0).toLocaleString()}</p>
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
          ))}
        </div>
      </DragDropContext>
    </div>
  );
}
