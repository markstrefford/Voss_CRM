import { useState } from 'react';
import { generateEmailDraft } from '@/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, Loader2, Sparkles } from 'lucide-react';

interface EmailDraftModalProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  contactId: string;
  dealId?: string;
}

export function EmailDraftModal({ open, onOpenChange, contactId, dealId }: EmailDraftModalProps) {
  const [intent, setIntent] = useState('');
  const [tone, setTone] = useState('professional');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateEmailDraft({ contact_id: contactId, deal_id: dealId, intent, tone });
      setSubject(res.data.subject);
      setBody(res.data.body);
    } catch {
      setBody('Failed to generate draft. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader><DialogTitle>Draft Email with AI</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label>What do you want to say?</Label>
              <Input value={intent} onChange={e => setIntent(e.target.value)} placeholder="e.g. Follow up on our meeting, send a proposal..." />
            </div>
            <div className="space-y-2">
              <Label>Tone</Label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {['professional', 'friendly', 'casual', 'formal'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={handleGenerate} disabled={generating || !intent} className="w-full">
                {generating ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Sparkles className="h-4 w-4 mr-1" />}
                Generate
              </Button>
            </div>
          </div>

          {(subject || body) && (
            <>
              <div className="space-y-2">
                <Label>Subject</Label>
                <Input value={subject} onChange={e => setSubject(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Body</Label>
                <Textarea value={body} onChange={e => setBody(e.target.value)} rows={10} />
              </div>
            </>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
          {body && (
            <Button onClick={handleCopy}>
              <Copy className="h-4 w-4 mr-1" />
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
