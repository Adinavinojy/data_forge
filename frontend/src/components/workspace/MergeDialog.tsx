import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';

interface MergeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentDatasetId: string;
  onMerge: (params: any) => void;
}

interface Dataset {
  id: string;
  original_filename: string;
  row_count: number;
  col_count: number;
}

export function MergeDialog({ open, onOpenChange, currentDatasetId, onMerge }: MergeDialogProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [mergeType, setMergeType] = useState<string>('inner');
  const [leftKey, setLeftKey] = useState<string>('');
  const [rightKey, setRightKey] = useState<string>('');

  useEffect(() => {
    if (open) {
      fetchDatasets();
    }
  }, [open]);

  const fetchDatasets = async () => {
    try {
      const res = await api.get('/datasets/');
      // Filter out current dataset
      setDatasets(res.data.filter((d: Dataset) => d.id !== currentDatasetId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMerge = () => {
    if (!selectedDatasetId) return;
    
    const params: any = {
      secondary_dataset_id: selectedDatasetId,
      how: mergeType
    };

    if (mergeType !== 'concat') {
       if (leftKey) params.left_on = leftKey;
       if (rightKey) params.right_on = rightKey;
       // If only one key provided, assume same name? Or force both?
       // Let's force both for clarity in this dialog, or if user leaves empty we assume index merge?
       // For now, let's just pass what we have.
    } else {
        params.axis = 0; // Default vertical concat
    }

    onMerge(params);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#1e1e1e] border-black text-gray-300 sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-gray-100">Merge Datasets</DialogTitle>
          <DialogDescription className="text-gray-500">
            Combine this dataset with another one.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Select Dataset to Merge</Label>
            <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
              <SelectTrigger className="bg-[#2d2d2d] border-black/50 text-gray-300">
                <SelectValue placeholder="Select a dataset..." />
              </SelectTrigger>
              <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                {datasets.map(d => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.original_filename} ({d.row_count} rows)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label>Merge Method</Label>
            <Select value={mergeType} onValueChange={setMergeType}>
              <SelectTrigger className="bg-[#2d2d2d] border-black/50 text-gray-300">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#2d2d2d] border-black/50 text-gray-300">
                <SelectItem value="inner">Inner Join (Intersection)</SelectItem>
                <SelectItem value="left">Left Join (Keep current)</SelectItem>
                <SelectItem value="right">Right Join (Keep new)</SelectItem>
                <SelectItem value="outer">Outer Join (Union of keys)</SelectItem>
                <SelectItem value="concat">Concatenate (Append rows)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {mergeType !== 'concat' && (
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Left Key (Current)</Label>
                <Input 
                  value={leftKey} 
                  onChange={(e) => setLeftKey(e.target.value)} 
                  placeholder="Column name"
                  className="bg-[#2d2d2d] border-black/50 text-gray-300"
                />
              </div>
              <div className="grid gap-2">
                <Label>Right Key (New)</Label>
                <Input 
                  value={rightKey} 
                  onChange={(e) => setRightKey(e.target.value)} 
                  placeholder="Column name"
                  className="bg-[#2d2d2d] border-black/50 text-gray-300"
                />
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} className="bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300">Cancel</Button>
          <Button onClick={handleMerge} disabled={!selectedDatasetId} className="bg-teal-600 hover:bg-teal-700 text-white">Merge</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
