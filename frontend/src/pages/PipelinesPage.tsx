import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Play, Edit, Clock, Download, Upload } from 'lucide-react';

interface Pipeline {
  id: string;
  name: string;
  description?: string;
  dataset_id: string;
  created_at: string;
  updated_at: string;
  steps: string; // JSON string
}

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = async () => {
    try {
      const response = await api.get('/pipelines/');
      setPipelines(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (pipeline: Pipeline) => {
    try {
      const res = await api.get(`/pipelines/${pipeline.id}/export`);
      const data = JSON.stringify(res.data, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${pipeline.name.replace(/\s+/g, '_')}_pipeline.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Export failed", err);
      alert("Failed to export pipeline");
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        await api.post('/pipelines/import', json);
        fetchPipelines(); // Refresh list
        alert("Pipeline template imported successfully!");
      } catch (err) {
        console.error("Import failed", err);
        alert("Invalid pipeline file");
      }
    };
    reader.readAsText(file);
  };

  if (loading) return <div className="p-8 text-center text-muted-foreground">Loading pipelines...</div>;

  return (
    <div className="container mx-auto p-8 space-y-8 bg-[#121212] min-h-screen text-gray-300">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
            <Link to="/">
            <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white hover:bg-white/10">
                <ArrowLeft className="h-5 w-5" />
            </Button>
            </Link>
            <div>
            <h1 className="text-2xl font-bold text-gray-100">Saved Pipelines</h1>
            <p className="text-sm text-gray-500">Resume your work or run existing pipelines</p>
            </div>
        </div>
        <div>
             <Button onClick={() => document.getElementById('pipeline-upload')?.click()} variant="outline" className="bg-[#1e1e1e] border-black/50 text-gray-300 hover:bg-[#2d2d2d] hover:text-white">
                <Upload className="mr-2 h-4 w-4" /> Import Template
            </Button>
            <input
                id="pipeline-upload"
                type="file"
                className="hidden"
                accept=".json"
                onChange={handleImport}
            />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pipelines.length === 0 ? (
          <div className="col-span-full text-center py-12 bg-[#1e1e1e] rounded-lg border border-black/50">
            <p className="text-gray-500">No pipelines found. Create one by editing a dataset.</p>
          </div>
        ) : (
          pipelines.map((pipeline) => (
            <Card key={pipeline.id} className="bg-[#1e1e1e] border-black/50 hover:border-gray-600 transition-colors flex flex-col">
              <CardHeader>
                <CardTitle className="text-lg text-gray-200">{pipeline.name}</CardTitle>
                <CardDescription className="text-gray-500 text-xs">
                  {pipeline.description || "No description"}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3" />
                    Updated: {new Date(pipeline.updated_at).toLocaleDateString()}
                  </div>
                  {pipeline.dataset_id && (
                    <div className="flex items-center gap-2">
                        <Edit className="h-3 w-3" />
                        Dataset: {pipeline.dataset_id.substring(0, 8)}...
                    </div>
                  )}
                  {!pipeline.dataset_id && (
                     <div className="flex items-center gap-2 text-teal-400">
                        <Upload className="h-3 w-3" />
                        Template (Unattached)
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2 border-t border-black/20 pt-4">
                {pipeline.dataset_id ? (
                    <Link to={`/datasets/${pipeline.dataset_id}`} className="flex-1">
                    <Button variant="secondary" className="w-full bg-[#2d2d2d] hover:bg-[#3e3e3e] text-gray-300">
                        <Play className="mr-2 h-3 w-3" /> Resume
                    </Button>
                    </Link>
                ) : (
                    <Button disabled variant="secondary" className="flex-1 bg-[#2d2d2d] text-gray-500 cursor-not-allowed">
                        Apply in Workspace
                    </Button>
                )}
                <Button variant="outline" size="icon" onClick={() => handleExport(pipeline)} className="bg-[#1e1e1e] border-black/50 text-gray-400 hover:text-white">
                    <Download className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
