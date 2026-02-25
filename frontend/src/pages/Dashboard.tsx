import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Upload, Database, GitBranch } from 'lucide-react';

interface Dataset {
  id: string;
  original_filename: string;
  created_at: string;
  row_count: number;
  col_count: number;
  size_bytes: number;
  file_format: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await api.get('/datasets/');
      setDatasets(response.data);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch datasets');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      await api.post('/datasets/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      fetchDatasets();
    } catch (err) {
      console.error(err);
      setError('Failed to upload dataset');
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8 space-y-8 bg-[#121212] min-h-screen text-gray-300">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-100">Dashboard</h1>
          <p className="text-gray-500">Manage your datasets and pipelines</p>
        </div>
        <div className="flex gap-3">
            <Link to="/pipelines">
                <Button variant="outline" className="bg-[#1e1e1e] border-black/50 text-gray-300 hover:bg-[#2d2d2d] hover:text-white">
                    <GitBranch className="mr-2 h-4 w-4" /> Saved Pipelines
                </Button>
            </Link>
            <Button onClick={() => document.getElementById('file-upload')?.click()} className="bg-teal-600 hover:bg-teal-700 text-white border-none">
            <Plus className="mr-2 h-4 w-4" /> New Dataset
            </Button>
            <input
            id="file-upload"
            type="file"
            className="hidden"
            accept=".csv,.xlsx,.xls,.json"
            onChange={handleFileUpload}
            />
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-900/50 text-red-200 p-4 rounded-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 rounded-xl bg-[#1e1e1e] animate-pulse border border-black/50" />
          ))}
        </div>
      ) : datasets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center border-2 border-dashed border-black/30 rounded-xl bg-[#1e1e1e]">
          <div className="bg-[#2d2d2d] p-4 rounded-full mb-4">
            <Upload className="h-8 w-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-200">No datasets yet</h3>
          <p className="text-sm text-gray-500 max-w-sm mt-2 mb-6">
            Upload a CSV, Excel, or JSON file to get started with data cleaning and transformation.
          </p>
          <Button onClick={() => document.getElementById('file-upload')?.click()} variant="secondary" className="bg-[#2d2d2d] text-gray-300 hover:bg-[#3e3e3e]">
            Upload File
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((dataset) => (
            <Card key={dataset.id} className="group transition-all hover:shadow-lg bg-[#1e1e1e] border-black/50 hover:border-gray-600">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="bg-teal-900/30 p-2 rounded-md">
                    <Database className="h-5 w-5 text-teal-500" />
                  </div>
                  <span className="text-xs font-mono text-gray-500 bg-black/30 px-2 py-1 rounded">
                    {dataset.file_format.toUpperCase()}
                  </span>
                </div>
                <CardTitle className="text-lg mt-3 truncate text-gray-200" title={dataset.original_filename}>
                  {dataset.original_filename}
                </CardTitle>
                <CardDescription className="text-xs text-gray-500">
                  Uploaded {new Date(dataset.created_at).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-3">
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                  <div className="flex flex-col bg-[#252526] p-2 rounded border border-black/20">
                    <span className="text-[10px] text-gray-600 uppercase">Rows</span>
                    <span className="font-mono font-medium">{dataset.row_count.toLocaleString()}</span>
                  </div>
                  <div className="flex flex-col bg-[#252526] p-2 rounded border border-black/20">
                    <span className="text-[10px] text-gray-600 uppercase">Columns</span>
                    <span className="font-mono font-medium">{dataset.col_count}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-3 border-t border-black/20">
                <Button 
                  variant="secondary" 
                  className="w-full bg-[#2d2d2d] hover:bg-[#3e3e3e] text-gray-300"
                  onClick={() => navigate(`/datasets/${dataset.id}`)}
                >
                  Open Workspace
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
