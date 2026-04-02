import { useEffect, useMemo, useState } from "react";
import { Wind, Thermometer, Droplets, MapPin, Clock, Database, AlertCircle } from "lucide-react";
import { GiPoisonGas } from "react-icons/gi";
import { WiBarometer } from "react-icons/wi";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ComposedChart, Area} from "recharts";

interface IndoorCurrentResponse {
  recorded_at_utc: string;
  source_id: string;
  latitude: number | null;
  longitude: number | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
}

interface IndoorHistoryItem {
  recorded_at_utc: string;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
}

interface IndoorHistoryResponse {
  source_id: string | null;
  from_utc: string;
  to_utc: string;
  items: IndoorHistoryItem[];
}

interface OutdoorCurrentResponse {
  recorded_at_utc: string;
  source_time_utc: string | null;
  aqi: number | null;
  dominant_pollutant: string | null;
  city_name: string | null;
  latitude: number | null;
  longitude: number | null;
  co: number | null;
  h: number | null;
  no2: number | null;
  o3: number | null;
  p: number | null;
  pm25: number | null;
  so2: number | null;
  t: number | null;
  w: number | null;
  is_dominant_pollutant?: (pollutant: string) => boolean;
}

interface OutdoorHistoryItem {
  recorded_at_utc: string;
  source_time_utc: string | null;
  aqi: number | null;
  dominant_pollutant: string | null;
  city_name: string | null;
  latitude: number | null;
  longitude: number | null;
  co: number | null;
  h: number | null;
  no2: number | null;
  o3: number | null;
  p: number | null;
  pm25: number | null;
  so2: number | null;
  t: number | null;
  w: number | null;
  is_dominant_pollutant?: (pollutant: string) => boolean;
}

interface OutdoorHistoryResponse {
  from_utc: string;
  to_utc: string;
  items: OutdoorHistoryItem[];
}

interface ForecastPollutant {
  pollutant: string;
  avg: number | null;
  min: number | null;
  max: number | null;
}

interface OutdoorForecastByDateResponse {
  source_time_utc: string | null;
  city_name: string | null;
  forecast: Record<string, ForecastPollutant[]>;
}

interface ForecastChartPoint {
  forecast_date: string;
  o3MinMax: [number, number];
  pm25MinMax: [number, number];
  pm10MinMax: [number, number];
  uviMinMax: [number, number];
}

interface IndoorChartPoint {
  time: string;
  recorded_at_utc: string;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
}

interface OutdoorChartPoint {
  time: string;
  recorded_at_utc: string;
  pm25: number | null;
  no2: number | null;
  o3: number | null;
  so2: number | null;
  co: number | null;
}

interface Pm25Status {
  label: string;
  note: string;
}


interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  dominant?: boolean;
  icon: React.ElementType;
}

interface StatCardBoardProps {
  title: string;
  statCards: StatCardProps[];
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

function formatChartDate(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;

  if (d.getHours() === 0) {
    return d.getDate().toString();
  }

  const day = d.getDate();
  const h = d.getHours();
  const ampm = h >= 12 ? "pm" : "am";
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${day}/${hour12}${ampm}`;
}

function classifyPm25(pm25: number | null | undefined): Pm25Status {
  if (pm25 == null || Number.isNaN(Number(pm25))) {
    return { label: "Unknown", note: "No PM2.5 reading available." };
  }
  const value = Number(pm25);
  if (value <= 12) return { label: "Good", note: "Air is in a generally comfortable range." };
  if (value <= 35) return { label: "Moderate", note: "Usually fine, but sensitive people may notice it." };
  if (value <= 55) return { label: "Elevated", note: "Worth monitoring, especially with respiratory issues." };
  if (value <= 150) return { label: "Unhealthy", note: "Limit exposure and consider a respirator outdoors." };
  return { label: "Very Unhealthy", note: "Avoid exposure where possible." };
}

function aggregateForecast(
  forecastByDate: Record<string, ForecastPollutant[]>
): ForecastChartPoint[] {
  return Object.entries(forecastByDate)
    .map(([forecast_date, pollutants]) => {
      const point: ForecastChartPoint = {
        forecast_date,
        o3MinMax: [0, 0],
        pm25MinMax: [0, 0],
        pm10MinMax: [0, 0],
        uviMinMax: [0, 0],
      };

      for (const p of pollutants) {
        const minMax: [number, number] = [p.min ?? 0, p.max ?? 0];

        switch (p.pollutant.toLowerCase()) {
          case "o3":
            point.o3MinMax = minMax;
            break;
          case "pm25":
            point.pm25MinMax = minMax;
            break;
          case "pm10":
            point.pm10MinMax = minMax;
            break;
          case "uvi":
            point.uviMinMax = minMax;
            break;
        }
      }

      return point;
    })
    .sort((a, b) => a.forecast_date.localeCompare(b.forecast_date));
}

export default function App(): React.JSX.Element {
  const BACKEND_URL =
    (import.meta.env.VITE_TOOL_URI as string) || "http://192.168.53.40:8009/api";

  const [current, setCurrent] = useState<IndoorCurrentResponse | null>(null);
  const [history, setHistory] = useState<IndoorHistoryItem[]>([]);
  const [waqiCurrent, setWaqiCurrent] = useState<OutdoorCurrentResponse | null>(null);
  const [waqiHistory, setWaqiHistory] = useState<OutdoorHistoryItem[]>([]);
  const [waqiForecast, setWaqiForecast] = useState<OutdoorForecastByDateResponse | null>(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  async function loadIndoor(url: string = BACKEND_URL): Promise<void> {
    const cleanUrl = url.replace(/\/$/, "");

    const currentUrl = new URL(`${cleanUrl}/v1/indoor/current`);
    const historyUrl = new URL(`${cleanUrl}/v1/indoor/history`);
    historyUrl.searchParams.set("days", "7");

    const [currentRes, historyRes] = await Promise.all([
      fetch(currentUrl.toString()),
      fetch(historyUrl.toString()),
    ]);

    if (!currentRes.ok) {
      throw new Error(`Indoor current request failed with ${currentRes.status}`);
    }
    if (!historyRes.ok) {
      throw new Error(`Indoor history request failed with ${historyRes.status}`);
    }

    const currentJson = (await currentRes.json()) as IndoorCurrentResponse;
    const historyJson = (await historyRes.json()) as IndoorHistoryResponse;

    setCurrent(currentJson);
    setHistory(Array.isArray(historyJson.items) ? historyJson.items : []);
  }

  async function loadOutdoor(url: string = BACKEND_URL): Promise<void> {
    const cleanUrl = url.replace(/\/$/, "");

    const currentUrl = new URL(`${cleanUrl}/v1/outdoor/current`);
    const historyUrl = new URL(`${cleanUrl}/v1/outdoor/history`);
    const forecastUrl = new URL(`${cleanUrl}/v1/outdoor/forecast/by-date`);
    historyUrl.searchParams.set("days", "7");

    const [currentRes, historyRes, forecastRes] = await Promise.all([
      fetch(currentUrl.toString()),
      fetch(historyUrl.toString()),
      fetch(forecastUrl.toString()),
    ]);

    if (!currentRes.ok) {
      throw new Error(`Outdoor current request failed with ${currentRes.status}`);
    }
    if (!historyRes.ok) {
      throw new Error(`Outdoor history request failed with ${historyRes.status}`);
    }
    if (!forecastRes.ok) {
      throw new Error(`Outdoor forecast request failed with ${forecastRes.status}`);
    }

    const currentJson = (await currentRes.json()) as OutdoorCurrentResponse;
    const historyJson = (await historyRes.json()) as OutdoorHistoryResponse;
    const forecastJson = (await forecastRes.json()) as OutdoorForecastByDateResponse;

    setWaqiCurrent(currentJson);
    setWaqiHistory(Array.isArray(historyJson.items) ? historyJson.items : []);
    setWaqiForecast(forecastJson);
  }

  async function loadAll(): Promise<void> {
    setError("");
    try {
      await Promise.all([loadIndoor(BACKEND_URL), loadOutdoor(BACKEND_URL)]);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load air quality data.");
    }
  }

  useEffect(() => {
    void loadAll();
    const timer = window.setInterval(() => {
      void loadAll();
    }, 30000);

    return () => window.clearInterval(timer);
  }, []);

  const pm25Status = useMemo(() => classifyPm25(current?.pm25), [current]);
  const outdoorPm25Status = useMemo(() => classifyPm25(waqiCurrent?.pm25), [waqiCurrent]);

  const latestCoordinates = useMemo(() => {
    if (current?.latitude == null || current?.longitude == null) return "-";
    return `${current.latitude.toFixed(4)}, ${current.longitude.toFixed(4)}`;
  }, [current]);

  const chartData = useMemo<IndoorChartPoint[]>(
    () =>
      history.map((row) => ({
        time: formatChartDate(row.recorded_at_utc),
        recorded_at_utc: row.recorded_at_utc,
        pm1: row.pm1,
        pm25: row.pm25,
        pm10: row.pm10,
        temperature_c: row.temperature_c,
        humidity_pct: row.humidity_pct,
      })),
    [history]
  );

  const waqiChartData = useMemo<OutdoorChartPoint[]>(
    () =>
      waqiHistory.map((row) => ({
        time: formatChartDate(row.recorded_at_utc),
        recorded_at_utc: row.recorded_at_utc,
        pm25: row.pm25,
        no2: row.no2,
        o3: row.o3,
        so2: row.so2,
        co: row.co,
      })),
    [waqiHistory]
  );

  const waqiForecastData = useMemo<ForecastChartPoint[]>(
    () => aggregateForecast(waqiForecast?.forecast ?? {}),
    [waqiForecast]
  );

  const activeStation = current?.source_id || "Unknown source";

  function StatCard({ title, value, subtitle, dominant = false, icon: Icon }: StatCardProps): React.JSX.Element {
    return (
      <div className="card">
        <div className="stat-card">
          <div>
            <div className="muted">{title}</div>
            <div className="stat-value">{value}</div>
            {subtitle ? <div className="muted small">{subtitle}</div> : null}
            {dominant && (    
              <div className="badge badge-highlight" style={{ marginTop: "6px", backgroundImage: "none" }}>
                Dominant pollutant
              </div>
            )}
          </div>
          <div className="icon-box">
            <Icon size={20} />
          </div>
        </div>
      </div>
    );
  }

  function StatCardBoard({title, statCards }: StatCardBoardProps): React.JSX.Element {
    return (
      <section className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-900">{title}</h1>

        <div className="stats-grid">
          {statCards.map((card, index) => (
            <StatCard
              key={card.title ?? `${card.title}-${index}`}
              {...card}
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <div className="page">
      <div className="container">
        <div className="header">
          <div>
            <h1>Air Quality Dashboard</h1>
            <p className="muted">A lightweight dashboard for your air quality data.</p>
          </div>
          <div className="header-actions">
          </div>
        </div>

        {error ? (
          <div className="error" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        ) : null}
          <StatCardBoard
            title="Indoors"
            statCards={[
              {
                title: "PM1 - Smallest airborne particles",
                value: current?.pm1 ?? "-",
                icon: Wind,
              },
              {
                title: "PM2.5 " + (pm25Status.label !== "Unknown" ? `(${pm25Status.label})` : ""),
                value: current?.pm25 ?? "-",
                icon: Wind,
              },
              {
                title: "PM10 - Larger airborne particles",
                value: current?.pm10 ?? "-",
                icon: Wind,
              },
              {
                title: "Temperature",
                value:
                  current?.temperature_c != null
                    ? `${Number(current.temperature_c).toFixed(1)} °C`
                    : "-",
                icon: Thermometer,
              },
              {
                title: "Humidity",
                value:
                  current?.humidity_pct != null
                    ? `${Number(current.humidity_pct).toFixed(1)} %`
                    : "-",
                icon: Droplets,
              },
            ]}
          />
          <StatCardBoard
            title="Outdoors"
            statCards={[
              {
                title: "PM2.5",
                value: waqiCurrent?.pm25 ?? "-",
                subtitle: outdoorPm25Status.note,
                dominant: waqiCurrent?.is_dominant_pollutant?.("pm25"),
                icon: Wind,
              },
              {
                title: "NO2 = Nitrogen dioxide",
                value: waqiCurrent?.no2 ?? "-",
                dominant: waqiCurrent?.is_dominant_pollutant?.("no2"),
                icon: GiPoisonGas,
              },
              {
                title: "O3 - Ozone",
                value: waqiCurrent?.o3 ?? "-",
                dominant: waqiCurrent?.is_dominant_pollutant?.("o3"),
                icon: GiPoisonGas,
              },
              {
                title: "SO2 - Sulfur dioxide",
                value: waqiCurrent?.so2 ?? "-",
                dominant: waqiCurrent?.is_dominant_pollutant?.("so2"),
                icon: GiPoisonGas,
              },
              {
                title: "CO - Carbon monoxide",
                value: waqiCurrent?.co ?? "-",
                dominant: waqiCurrent?.is_dominant_pollutant?.("co"),
                icon: GiPoisonGas,
              },
              {
                title: "Temperature",
                value:
                  waqiCurrent?.t != null
                    ? `${Number(waqiCurrent.t).toFixed(1)} °C`
                    : "-",
                icon: Thermometer,
              },
              {
                title: "Humidity",
                value:
                  waqiCurrent?.h != null
                    ? `${Number(waqiCurrent.h).toFixed(1)} %`
                    : "-",
                icon: Droplets,
              },
              {
                title: "Pressure",
                value:
                  waqiCurrent?.p != null
                    ? `${Number(waqiCurrent.p).toFixed(1)} hPa`
                    : "-",
                icon: WiBarometer,
              },
              {
                title: "Wind Speed",
                value:
                  waqiCurrent?.w != null
                    ? `${Number(waqiCurrent.w).toFixed(1)} m/s`
                    : "-",
                icon: Wind,
              }
            ]}
          />


        <div className="content-grid">
          <div className="card">
            <h2>Indoor Trend</h2>
            <p className="muted small">Recent history from /status/history</p>
            <div className="chart-wrap" style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(_, payload) =>
                      payload?.[0]?.payload?.recorded_at_utc
                        ? formatDate(payload[0].payload.recorded_at_utc)
                        : "-"
                    }
                  />
                  <Legend />
                  <Line type="monotone" dataKey="pm1" stroke="#6b7280" name="PM1" dot={false} />
                  <Line type="monotone" dataKey="pm25" stroke="#ef4444" name="PM2.5" dot={false} />
                  <Line type="monotone" dataKey="pm10" stroke="#f59e0b" name="PM10" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <h2>Outdoor Trend</h2>
            <div className="chart-wrap" style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <LineChart data={waqiChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(_, payload) =>
                      payload?.[0]?.payload?.recorded_at_utc
                        ? formatDate(payload[0].payload.recorded_at_utc)
                        : "-"
                    }
                  />
                  <Legend />
                  <Line type="monotone" dataKey="pm25" stroke="#ef4444" name="PM2.5" dot={false} />
                  <Line type="monotone" dataKey="o3" stroke="#a855f7" name="O3" dot={false} />
                  <Line type="monotone" dataKey="no2" stroke="#eab308" name="NO2" dot={false} />
                  <Line type="monotone" dataKey="so2" stroke="#3b82f6" name="SO2" dot={false} />
                  <Line type="monotone" dataKey="co" stroke="#14b8a6" name="CO" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          
            <h2>Forecast</h2>
            <div className="chart-wrap" style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <ComposedChart data={waqiForecastData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="forecast_date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area dataKey="pm25MinMax" 
                                      fill="#ef4444"
                          stroke="#ef4444"
                          fillOpacity={0.12}
                  name="PM2.5 range" />
                  <Area dataKey="o3MinMax" 
                                      fill="#a855f7"
                          stroke="#a855f7"
                          fillOpacity={0.12}
                  name="O3 range" />
                  <Area dataKey="pm10MinMax" 
                                      fill="#eab308"
                          stroke="#eab308"
                          fillOpacity={0.12}
                  name="PM10 range" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>            
          </div>
          <div className="side-column">
            <div className="card">
              <h2>Current station</h2>
              <div className="detail-row">
                <strong>Station:</strong> {activeStation}
              </div>
              <div className="detail-row">
                <MapPin size={16} /> {latestCoordinates}
              </div>
              <div className="detail-row">
                <Clock size={16} /> {formatDate(current?.recorded_at_utc)}
              </div>
              <div className="detail-row">
                <Database size={16} /> {formatDate(lastUpdated)}
              </div>
            </div>
            <div className="card">
              <h2>Recent records</h2>
              <div className="records">
                {history.length === 0 ? (
                  <div className="muted small">No historical data available yet.</div>
                ) : (
                  history
                    .slice()
                    .reverse()
                    .slice(0, 12)
                    .map((row, index) => (
                      <div key={`${row.recorded_at_utc}-${index}`} className="record">
                        <div className="record-title">{formatDate(row.recorded_at_utc)}</div>
                        <div className="record-grid">
                          <div>PM1: {row.pm1 ?? "-"}</div>
                          <div>PM2.5: {row.pm25 ?? "-"}</div>
                          <div>PM10: {row.pm10 ?? "-"}</div>
                          <div>Temp: {row.temperature_c ?? "-"} °C</div>
                          <div>Humidity: {row.humidity_pct ?? "-"} %</div>
                        </div>
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
