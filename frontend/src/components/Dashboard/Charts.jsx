import React from 'react';
import { BarChart3 } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

export default function Charts({ metrics }) {
  const timeComparisonData = [
    { name: 'Standard CI', time: metrics.standard_run_time_seconds },
    { name: 'Smart TIA', time: metrics.smart_run_time_seconds }
  ];
  const testBreakdownData = [
    { name: 'Executed', value: metrics.tests_executed, color: '#10b981' }, 
    { name: 'Skipped', value: metrics.tests_skipped, color: '#3f3f46' }    
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 relative shadow-sm">
         <div className="absolute top-0 right-0 p-4 opacity-10">
            <BarChart3 className="h-24 w-24 text-emerald-400" />
         </div>
         <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2 text-lg relative z-10">
            Time Comparison (Seconds)
         </h3>
         <div className="h-[250px] w-full relative z-10">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeComparisonData} layout="vertical" margin={{ top: 0, right: 40, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
              <XAxis type="number" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis dataKey="name" type="category" stroke="#a1a1aa" fontSize={13} tickLine={false} axisLine={false} width={90} />
              <Tooltip 
                cursor={{fill: '#27272a', opacity: 0.4}} 
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                itemStyle={{ color: '#10b981', fontWeight: 600 }}
              />
              <Bar dataKey="time" radius={[0, 6, 6, 0]} barSize={40}>
                {
                  timeComparisonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#3f3f46' : '#10b981'} />
                  ))
                }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
         </div>
      </div>

      <div className="bg-zinc-900/50 p-6 rounded-2xl border border-zinc-800 flex items-center relative shadow-sm">
        <div className="w-1/2 h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={testBreakdownData}
                innerRadius={65}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
                stroke="none"
              >
                {testBreakdownData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }}
                itemStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="w-1/2 pl-6 md:pl-10 space-y-5">
          <div>
            <h3 className="text-zinc-100 font-semibold text-lg mb-1">Suite Avoidance</h3>
            <p className="text-xs text-zinc-500 uppercase tracking-widest font-semibold text-balance">Intelligent Optimization</p>
          </div>
          <div className="space-y-4">
            {testBreakdownData.map((item, idx) => (
               <div key={idx} className="flex items-center gap-4">
                  <div className="w-4 h-4 rounded-md shadow-sm" style={{ backgroundColor: item.color }}></div>
                  <div>
                    <div className="text-zinc-400 text-sm font-medium">{item.name}</div>
                    <div className="text-2xl font-bold text-zinc-100">{item.value}</div>
                  </div>
               </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}