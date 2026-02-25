import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';

interface ApplyTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  datasetId: string;
  onApplied: () => void;
}

interface Pipeline {
  id: string;
  name: string;
  description?: string;
}

export function ApplyTemplateDialog({ open, onOpenChange, datasetId, onApplied }: ApplyTemplateDialogProps) {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipelineId, setSelectedPipelineId] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchPipelines();
    }
  }, [open]);

  const fetchPipelines = async () => {
    try {
      const res = await api.get('/pipelines/');
      setPipelines(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleApply = async () => {
    if (!selectedPipelineId) return;
    
    try {
      setLoading(true);
      await api.post(`/pipelines/${selectedPipelineId}/apply/${datasetId}`);
      onApplied();
      alert("Template applied successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to apply template. Check if columns match.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-gray-100">Apply Pipeline Template</DialogTitle>
          <DialogDescription className="text-gray-500">
            Select a saved pipeline to apply to this dataset. Warning: This will overwrite current steps.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Select Template</Label>
            <Select value={selectedPipelineId} onValueChange={setSelectedPipelineId}>
              <SelectTrigger className="bg-[#2d2d2d] border-black/50 text-gray-300">
                <SelectValue placeholder="Choose a pipeline..." />
              </SelectTrigger>
              <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                {pipelines.map(p => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
          <Button onClick={handleApply} disabled={!selectedPipelineId || loading} className="bg-teal-600 hover:bg-teal-700 text-white">
            {loading ? 'Applying...' : 'Apply Template'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
