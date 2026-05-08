"use client";
import { useState, useMemo } from 'react';
import schedule from '../data/schedule.json';

const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const STATUS_COLOR = {
  published: 'bg-green-500/20 border-green-500/40 text-green-300',
  scheduled: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300',
  draft: 'bg-blue-500/20 border-blue-500/40 text-blue-300',
  pending: 'bg-gray-500/20 border-gray-500/40 text-gray-400',
};
const VSCORE_COLOR = (v) => v >= 8 ? 'text-green-400' : v >= 6 ? 'text-yellow-400' : 'text-red-400';

export default function Home() {
  const [weekIndex, setWeekIndex] = useState(0);
  const [selected, setSelected] = useState(null);

  const week = schedule.weeks[weekIndex] || schedule.weeks[0];
  const totalSlots = week.days.reduce((acc, d) => acc + d.slots.length, 0);
  const publishedSlots = week.days.reduce((acc, d) => acc + d.slots.filter(s => s.status === 'published').length, 0);

  return (
    <main className="max-w-7xl mx-auto p-6 md:p-10">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-curio-accent">
              📅 CurioClip — Calendario
            </h1>
            <p className="text-gray-400 mt-1">
              Programación semanal × sub-niches rotativos × horarios algorítmicos
            </p>
          </div>
          <div className="flex gap-3 items-center">
            <button
              onClick={() => setWeekIndex(Math.max(0, weekIndex - 1))}
              disabled={weekIndex === 0}
              className="px-4 py-2 bg-curio-panel border border-gray-700 rounded-lg hover:border-curio-accent disabled:opacity-30"
            >← Anterior</button>
            <div className="text-center min-w-[200px]">
              <div className="font-bold text-lg">{week.label}</div>
              <div className="text-xs text-gray-500">{week.dateRange}</div>
            </div>
            <button
              onClick={() => setWeekIndex(Math.min(schedule.weeks.length - 1, weekIndex + 1))}
              disabled={weekIndex === schedule.weeks.length - 1}
              className="px-4 py-2 bg-curio-panel border border-gray-700 rounded-lg hover:border-curio-accent disabled:opacity-30"
            >Siguiente →</button>
          </div>
        </div>

        {/* KPIs barra */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
          <Kpi label="Slots semana" value={totalSlots} />
          <Kpi label="Publicados" value={publishedSlots} accent="green" />
          <Kpi label="Programados" value={totalSlots - publishedSlots} accent="yellow" />
          <Kpi label="V-Score promedio" value={(week.avgVScore || 0).toFixed(2)} accent="accent" />
          <Kpi label="Sub-niches" value={Array.from(new Set(week.days.flatMap(d => d.slots.map(s => s.subNiche)))).length} />
        </div>
      </header>

      {/* Grid semanal */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
        {week.days.map((day) => (
          <div key={day.dayName} className="bg-curio-panel/60 border border-gray-800 rounded-xl p-3 min-h-[300px]">
            <div className="text-center pb-3 border-b border-gray-800 mb-3">
              <div className="font-bold text-curio-accent">{day.dayName}</div>
              <div className="text-xs text-gray-500">{day.date}</div>
              {day.subNicheTheme && (
                <div className="text-[10px] mt-1 text-gray-400 uppercase tracking-wider">{day.subNicheTheme}</div>
              )}
            </div>
            <div className="space-y-2">
              {day.slots.length === 0 && (
                <div className="text-xs text-gray-600 italic text-center py-8">Sin slots</div>
              )}
              {day.slots.map((slot, i) => (
                <button
                  key={i}
                  onClick={() => setSelected(slot)}
                  className={`w-full text-left p-2 rounded-lg border ${STATUS_COLOR[slot.status]} hover:scale-[1.02] transition`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm">{slot.time}</span>
                    <span className="text-[10px] uppercase opacity-70">{slot.platform}</span>
                  </div>
                  <div className="text-xs mt-1 line-clamp-2 opacity-90">{slot.title}</div>
                  {slot.vScore != null && (
                    <div className={`text-[11px] mt-1 font-bold ${VSCORE_COLOR(slot.vScore)}`}>
                      V-Score: {slot.vScore.toFixed(2)}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Modal de detalle */}
      {selected && <DetailModal slot={selected} onClose={() => setSelected(null)} />}

      {/* Footer info */}
      <footer className="mt-10 text-center text-xs text-gray-600">
        <p>Sistema CurioClip · Calendario auto-generado · Última actualización: {schedule.lastUpdated}</p>
        <p className="mt-1">Pipeline: Outlier Cloning → Auto-editor → V-Score → Compliance → Publicación</p>
      </footer>
    </main>
  );
}

function Kpi({ label, value, accent }) {
  const colorMap = { green: 'text-green-400', yellow: 'text-yellow-400', accent: 'text-curio-accent', red: 'text-red-400' };
  return (
    <div className="bg-curio-panel/40 border border-gray-800 rounded-lg p-3">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${colorMap[accent] || 'text-white'}`}>{value}</div>
    </div>
  );
}

function DetailModal({ slot, onClose }) {
  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-curio-panel max-w-3xl w-full max-h-[90vh] overflow-y-auto rounded-2xl border border-curio-accent/30 glow scrollbar-curio"
      >
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <div className="text-xs text-curio-accent uppercase tracking-wider mb-1">{slot.subNiche}</div>
              <h2 className="text-2xl font-bold">{slot.title}</h2>
              <div className="text-sm text-gray-400 mt-1">
                {slot.day} · {slot.time} · {slot.platform}
              </div>
            </div>
            <button onClick={onClose} className="text-2xl text-gray-500 hover:text-white">×</button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Thumbnail / video preview */}
            <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden border border-gray-800">
              {slot.thumbnail ? (
                <img src={slot.thumbnail} alt={slot.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-600 text-sm">
                  Sin thumbnail
                </div>
              )}
            </div>

            {/* Detalles */}
            <div className="space-y-4">
              {slot.vScore != null && (
                <div className="bg-black/40 rounded-lg p-3">
                  <div className="text-xs text-gray-500 uppercase mb-1">V-Score</div>
                  <div className={`text-3xl font-bold ${VSCORE_COLOR(slot.vScore)}`}>{slot.vScore.toFixed(2)}/10</div>
                  {slot.decision && (
                    <div className="text-xs mt-1 opacity-70">{slot.decision}</div>
                  )}
                </div>
              )}

              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Caption</div>
                <div className="text-sm bg-black/40 rounded-lg p-3 whitespace-pre-wrap leading-relaxed">
                  {slot.caption || '—'}
                </div>
              </div>

              <div>
                <div className="text-xs text-gray-500 uppercase mb-1">Hashtags</div>
                <div className="flex flex-wrap gap-2">
                  {(slot.hashtags || []).map(h => (
                    <span key={h} className="bg-curio-accent/10 text-curio-accent text-xs px-2 py-1 rounded">{h}</span>
                  ))}
                </div>
              </div>

              {slot.realMetrics && (
                <div>
                  <div className="text-xs text-gray-500 uppercase mb-1">Métricas reales</div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <Stat label="Views" value={slot.realMetrics.views} />
                    <Stat label="Likes" value={slot.realMetrics.likes} />
                    <Stat label="Saves" value={slot.realMetrics.saves} />
                  </div>
                </div>
              )}

              {slot.predictedMetrics && (
                <div>
                  <div className="text-xs text-gray-500 uppercase mb-1">Métricas predichas (sim)</div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <Stat label="Hook %" value={`${slot.predictedMetrics.hookRate}%`} />
                    <Stat label="Save %" value={`${slot.predictedMetrics.saveRate}%`} />
                    <Stat label="Share %" value={`${slot.predictedMetrics.shareRate}%`} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-black/40 rounded p-2">
      <div className="text-[10px] text-gray-500 uppercase">{label}</div>
      <div className="font-bold">{value}</div>
    </div>
  );
}
