import { Button } from '@/components/ui/button';
import { RotateCcw } from 'lucide-react';
import { useRef, useEffect, useState } from 'react';

interface Step {
  step_id?: string;
  operation: string;
  params: any;
  timestamp?: string;
}

interface LogPanelProps {
  steps: Step[];
  onRemoveStep: (index: number) => void;
  onReset: () => void;
  onCommand?: (cmd: string) => void;
}

export function LogPanel({ steps, onRemoveStep, onReset, onCommand }: LogPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [command, setCommand] = useState('');
  const [initTime] = useState(() => new Date().toLocaleTimeString('en-US', { hour12: false }));
  const [lastUpdateTime, setLastUpdateTime] = useState(initTime);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    if (steps.length > 0) {
      setLastUpdateTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }
  }, [steps]);

  const handleCommand = () => {
    if (command.trim() && onCommand) {
      onCommand(command.trim());
      setCommand('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCommand();
    }
  };

  const formatTimestamp = (isoString?: string) => {
    if (!isoString) return initTime;
    return new Date(isoString).toLocaleTimeString('en-US', { hour12: false });
  };

  return (
    <div className="h-64 border-t border-border bg-black text-xs font-mono flex flex-col">
      <div className="flex items-center justify-between px-3 py-1 bg-muted/20 border-b border-border">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="font-semibold">Console & Commands</span>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onReset} disabled={steps.length === 0} className="h-6 text-[10px] text-muted-foreground hover:text-white px-2">
            <RotateCcw className="h-3 w-3 mr-1" /> Clear Console
          </Button>
        </div>
      </div>

      <div className="flex items-center px-2 py-1 border-b border-border/20 bg-background">
        <span className="text-muted-foreground mr-2">Command:</span>
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          className="bg-transparent border-none outline-none flex-1 text-green-400 placeholder:text-muted-foreground/30"
          placeholder="Type a natural language command (e.g. 'convert age to string', 'drop duplicates')..."
        />
        <Button variant="secondary" size="sm" className="h-6 text-[10px] px-2" onClick={handleCommand} disabled={!command.trim()}>Execute</Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 space-y-1 font-mono">
        <div className="text-muted-foreground">
          [{formatTimestamp()}] System initialized - 100% offline mode
        </div>
        <div className="text-muted-foreground">
          [{formatTimestamp()}] Ready for data processing operations
        </div>

        {steps.map((step, i) => (
          <div key={i} className="flex group hover:bg-white/5 p-0.5 -mx-2 px-2">
            <span className="text-muted-foreground min-w-[80px] select-none">[{formatTimestamp(step.timestamp)}]</span>
            <span className="text-green-400 mr-2">➜</span>
            <span className="text-white mr-2">Applied {step.operation}</span>
            <span className="text-muted-foreground">
              {Object.entries(step.params).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(' ')}
            </span>
            <button
              onClick={() => onRemoveStep(i)}
              className="ml-auto text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              [UNDO]
            </button>
          </div>
        ))}
        {steps.length > 0 && (
          <div className="text-green-500">
            [{steps[steps.length - 1]?.timestamp ? formatTimestamp(steps[steps.length - 1].timestamp) : lastUpdateTime}] Pipeline updated successfully ({steps.length} steps active)
          </div>
        )}
      </div>
    </div>
  );
}
