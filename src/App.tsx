import { useEffect, useMemo, useState } from "react";
import { Wind, Thermometer, Droplets, MapPin, Clock, Database, AlertCircle } from "lucide-react";
import { GiPoisonGas } from "react-icons/gi";
import { WiBarometer } from "react-icons/wi";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ComposedChart, Area} from "recharts";


// Type definitions
interface AirQualityReading {
  timestamp_utc: string;
  station_id: string | null;
  pm1: number | null;
  pm25: number | null;
  pm10: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
  lat: number | null;
  lon: number | null;
  source_json: string;
}

interface Pm25Status {
  label: string;
  note: string;
}

interface ChartDataPoint {
  time: string;
  timestamp_utc: string;
  pm25: number | null;
  pm10: number | null;
  pm1: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
}

interface WaqiChartDataPoint {
  time: string;
  timestamp_utc: string;
  pm25: number | null;
  no2: number | null;
  o3: number | null;
  so2: number | null;
  co: number | null;
}

interface Device {
  station_id: string;
  name?: string;
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

interface WaqiReading {
  timestamp_utc: string;
  waqi_status: string | null;
  aqi: number | null;
  dominant_pollutant: string | null;
  station_name: string | null;
  station_uid: number | null;
  station_lat: number | null;
  station_lon: number | null;
  station_url: string | null;
  measurement_time: string | null;
  pm25: number | null;
  no2: number | null;
  o3: number | null;
  so2: number | null;
  co: number | null;
  t: number | null;
  h: number | null;
  p: number | null;
  w: number | null;
  source_json: string;
  is_dominant_pollutant?: (pollutant: string) => boolean;
}

interface WaqiForecastRow {
  forecast_date: string;
  pollutant: string;
  station_name: string | null;
  station_uid: number | null;  
  avg: number | null;
  min: number | null;
  max: number | null;

}

interface WaqiForecastDataPoint {
  forecast_date: string;
  station_name: string | null;
  station_uid: number | null;
  o3MinMax: number[];
  pm25MinMax: number[];
  pm10MinMax: number[];
  uviMinMax: number[];
}

function aggregateForecast(rows: WaqiForecastRow[]): WaqiForecastDataPoint[] {
  const map = new Map<string, WaqiForecastDataPoint>();

  for (const row of rows) {
    const key = row.forecast_date;

    if (!map.has(key)) {
      map.set(key, {
        forecast_date: row.forecast_date,
        station_name: row.station_name,
        station_uid: row.station_uid,
        o3MinMax: [],
        pm25MinMax: [],
        pm10MinMax: [],
        uviMinMax: [],
      });
    }

    const entry = map.get(key)!;
    const minMax = [row.min != null ? row.min : 0, row.max != null ? row.max : 0]
    console.debug(entry + "updating " + row.pollutant + " minMax: " + minMax)

    switch (row.pollutant.toLowerCase()) {
      case "o3":
        entry.o3MinMax = minMax;
        break;
      case "pm25":
        entry.pm25MinMax =  minMax;
        break;
      case "pm10":
        entry.pm10MinMax =  minMax;
        break;
      case "uvi":
        entry.uviMinMax =  minMax;
        break;
    }
  }

  console.debug("Cloud Chart");
  console.debug(Array.from(map.values()));

  return Array.from(map.values()).sort((a, b) =>
    a.forecast_date.localeCompare(b.forecast_date)
  );
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

function formatChartDate(ts: string): string {
    const d = new Date(ts);

    if (d.getHours() === 0) {
      return d.getDate().toString();
    }

    const h = d.getHours();
    const ampm = h >= 12 ? "pm" : "am";
    const hour12 = h % 12 === 0 ? 12 : h % 12;

    return `${hour12}${ampm}`;
}

function classifyPm25(pm25: number | null | undefined): Pm25Status {
  if (pm25 === null || pm25 === undefined || Number.isNaN(Number(pm25))) {
    return { label: "Unknown", note: "No PM2.5 reading available." };
  }

  const value = Number(pm25);
  if (value <= 12) return { label: "Good", note: "Air is in a generally comfortable range." };
  if (value <= 35) return { label: "Moderate", note: "Usually fine, but sensitive people may notice it." };
  if (value <= 55) return { label: "Elevated", note: "Worth monitoring, especially with respiratory issues." };
  if (value <= 150) return { label: "Unhealthy", note: "Limit exposure and consider a respirator outdoors." };
  return { label: "Very Unhealthy", note: "Avoid exposure where possible." };
}

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
    <section className="space-y-6">
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

export default function App() {
  const BACKEND_URL = (import.meta.env.VITE_TOOL_URI as string) || "http://localhost:8008";
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [current, setCurrent] = useState<AirQualityReading | null>(null);
  const [history, setHistory] = useState<AirQualityReading[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [devicesLoading, setDevicesLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [waqiCurrent, setWaqiCurrent] = useState<WaqiReading | null>(null);
  const [waqiHistory, setWaqiHistory] = useState<WaqiReading[]>([]);
  const [waqiForecast, setWaqiForecast] = useState<WaqiForecastRow[]>([]);

  async function loadWaqi(url: string = BACKEND_URL): Promise<void> {
    const cleanUrl = url.replace(/\/$/, "");
    const currentUrl = new URL(`${cleanUrl}/waqi/current`);
    const historyUrl = new URL(`${cleanUrl}/waqi/history`);
    const forecastUrl = new URL(`${cleanUrl}/waqi/forecast`);
    historyUrl.searchParams.set("limit", "100000");

    const [currentRes, historyRes, forecastRes] = await Promise.all([
      fetch(currentUrl.toString()),
      fetch(historyUrl.toString()),
      fetch(forecastUrl.toString()),
    ]);

    if (currentRes.ok) {
      const currentJson = (await currentRes.json()) as WaqiReading;
      currentJson.is_dominant_pollutant = (pollutant: string): boolean => {
        if (!pollutant) return false;
        return currentJson.dominant_pollutant?.toLowerCase() === pollutant.toLowerCase();
      };
      setWaqiCurrent(currentJson);
    }

    if (historyRes.ok) {
      const historyJson = await historyRes.json();
      setWaqiHistory(Array.isArray(historyJson) ? [...historyJson].reverse() : []);
    }

    if (forecastRes.ok) {
      const forecastJson = await forecastRes.json();
      setWaqiForecast(Array.isArray(forecastJson) ? [...forecastJson].reverse()  : []);
    }
  }

  async function loadDevices(url: string = BACKEND_URL, preserveSelection: boolean = true): Promise<Device[]> {
    setDevicesLoading(true);
    try {
      const devicesUrl = `${url.replace(/\/$/, "")}/devices`;
      const response = await fetch(devicesUrl);
      if (!response.ok) {
        throw new Error(`Devices request failed with ${response.status}`);
      }
      const data = await response.json();
      const list = Array.isArray(data) ? data : data.devices || [];
      setDevices(list);

      if (list.length === 0) {
        setSelectedDeviceId("");
        return [];
      }

      const hasExisting = preserveSelection && list.some((device: Device) => device.station_id === selectedDeviceId);
      if (!hasExisting) {
        setSelectedDeviceId(list[0].station_id || "");
      }

      return list;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load devices.");
      return [];
    } finally {
      setDevicesLoading(false);
    }
  }

  async function loadData(url: string = BACKEND_URL, requestedDeviceId: string = selectedDeviceId): Promise<void> {
    setLoading(true);
    setError("");

    try {
      const cleanUrl = url.replace(/\/$/, "");
      const currentUrl = new URL(`${cleanUrl}/status/current`);
      const historyUrl = new URL(`${cleanUrl}/status/history`);
      historyUrl.searchParams.set("limit", "100000");

      if (requestedDeviceId.trim()) {
        currentUrl.searchParams.set("station_id", requestedDeviceId.trim());
        historyUrl.searchParams.set("station_id", requestedDeviceId.trim());
      }

      const [currentRes, historyRes] = await Promise.all([
        fetch(currentUrl.toString()),
        fetch(historyUrl.toString()),
      ]);

      if (!currentRes.ok) {
        throw new Error(`Current status request failed with ${currentRes.status}`);
      }
      if (!historyRes.ok) {
        throw new Error(`History request failed with ${historyRes.status}`);
      }

      const [currentJson, historyJson] = await Promise.all([
        currentRes.json(),
        historyRes.json(),
      ]);

      setCurrent(currentJson);
      setHistory(Array.isArray(historyJson) ? [...historyJson].reverse() : []);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load air quality data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function bootstrap(): Promise<void> {
      const list = await loadDevices(BACKEND_URL, false);
      if (cancelled) return;

      const firstId = list?.[0]?.station_id || "";
      setSelectedDeviceId(firstId);

      await Promise.all([
        loadData(BACKEND_URL, firstId),
        loadWaqi(BACKEND_URL),
      ]);
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, [BACKEND_URL]);

  useEffect(() => {
    const timer = setInterval(() => {
      loadData(BACKEND_URL, selectedDeviceId);
      loadWaqi(BACKEND_URL);
    }, 30000);

    return () => clearInterval(timer);
  }, [BACKEND_URL, selectedDeviceId]);

  useEffect(() => {
    if (!selectedDeviceId) return;
    loadData(BACKEND_URL, selectedDeviceId);
  }, [BACKEND_URL, selectedDeviceId]);

  const pm25Status = useMemo(() => classifyPm25(current?.pm25), [current]);
  const outdoorPm25Status = useMemo(() => classifyPm25(waqiCurrent?.pm25), [waqiCurrent]);

  const latestCoordinates = useMemo(() => {
    if (current?.lat == null || current?.lon == null) return "-";
    return `${Number(current.lat).toFixed(4)}, ${Number(current.lon).toFixed(4)}`;
  }, [current]);

  const chartData = useMemo((): ChartDataPoint[] => {
    return history.map((row) => ({
      time: formatChartDate(row.timestamp_utc),
      timestamp_utc: row.timestamp_utc,
      pm25: row.pm25,
      pm10: row.pm10,
      pm1: row.pm1,
      temperature_c: row.temperature_c,
      humidity_pct: row.humidity_pct,
    }));
  }, [history]);

  const waqiChartData = useMemo((): WaqiChartDataPoint[] => {
    return waqiHistory.map((row) => ({
      time: formatChartDate(row.timestamp_utc),
      timestamp_utc: row.timestamp_utc,
      pm25: row.pm25,
      no2: row.no2,
      o3: row.o3,
      so2: row.so2,
      co: row.co,
    }));
  }, [waqiHistory]);

  const waqiForecastData = useMemo((): WaqiForecastDataPoint[] => {
    return aggregateForecast(waqiForecast);
  }, [waqiForecast]);

  const activeStation = current?.station_id || selectedDeviceId || "Unknown station";

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

        <div className="card">
          <h2>Connection</h2>
          <div className="connection-grid">
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              style={{
                padding: "8px 12px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                fontSize: "14px",
              }}
              disabled={devicesLoading || devices.length === 0}
            >
              {devices.length === 0 ? (
                <option value="">No devices found</option>
              ) : (
                devices.map((device) => (
                  <option key={device.station_id} value={device.station_id}>
                    {device.name || device.station_id}
                  </option>
                ))
              )}
            </select>
            <button
              className="button"
              onClick={async () => {
                await loadDevices(BACKEND_URL);
                await loadData(BACKEND_URL, selectedDeviceId);
              }}
              disabled={loading || devicesLoading}
            >
              Refresh devices
            </button>
            <span className="badge badge-good" style={{ backgroundImage: pm25Status.label === "Good" ? "" : "none" }}>
              {pm25Status.label}
            </span>
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
                title: "PM1",
                value: current?.pm1 ?? "-",
                subtitle: "Fine airborne particles",
                icon: Wind,
              },
              {
                title: "PM2.5",
                value: current?.pm25 ?? "-",
                subtitle: pm25Status.note,
                icon: Wind,
              },
              {
                title: "PM10",
                value: current?.pm10 ?? "-",
                subtitle: "Larger airborne particles",
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
                title: "NO2",
                value: waqiCurrent?.no2 ?? "-",
                subtitle: "Nitrogen dioxide",
                dominant: waqiCurrent?.is_dominant_pollutant?.("no2"),
                icon: GiPoisonGas,
              },
              {
                title: "O3",
                value: waqiCurrent?.o3 ?? "-",
                subtitle: "Ozone",
                dominant: waqiCurrent?.is_dominant_pollutant?.("o3"),
                icon: GiPoisonGas,
              },
              {
                title: "SO2",
                value: waqiCurrent?.so2 ?? "-",
                subtitle: "Sulfur dioxide",
                dominant: waqiCurrent?.is_dominant_pollutant?.("so2"),
                icon: GiPoisonGas,
              },
              {
                title: "CO",
                value: waqiCurrent?.co ?? "-",
                subtitle: "Carbon monoxide",
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
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" />
                  <XAxis
                    dataKey="time"
                    minTickGap={32}
                    stroke="#b8c1d1"
                  />
                  <YAxis stroke="#b8c1d1" />
                  <Tooltip
                    formatter={(value: any, name: any) => [value, String(name).toUpperCase()]}
                    labelFormatter={(_: any, payload: any) =>
                      payload?.[0]?.payload?.timestamp_utc
                        ? formatDate(payload[0].payload.timestamp_utc)
                        : "-"
                    }
                  />
                  <Legend verticalAlign="top" align="center" height={28} />
                  <Line type="monotone" dataKey="pm25" stroke="#ef4444" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="pm10" stroke="#eab308" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="pm1" stroke="#a855f7" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <h2>Outdoor Trend</h2>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={waqiChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" />
                  <XAxis
                    dataKey="time"
                    minTickGap={32}
                    stroke="#b8c1d1"
                  />
                  <YAxis stroke="#b8c1d1" />
                  <Tooltip
                    formatter={(value: any, name: any) => [value, String(name).toUpperCase()]}
                    labelFormatter={(_: any, payload: any) =>
                      payload?.[0]?.payload?.timestamp_utc
                        ? formatDate(payload[0].payload.timestamp_utc)
                        : "-"
                    }
                  />
                  <Legend verticalAlign="top" align="center" height={28} />
                  <Line type="monotone" dataKey="pm25" stroke="#ef4444" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="no2" stroke="#eab308" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="o3" stroke="#a855f7" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="so2" stroke="#3b82f6" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="co" stroke="#14b8a6" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>            
            <h2>Forecast</h2>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                    data={waqiForecastData}
                    margin={{
                      top: 20,
                      right: 0,
                      bottom: 0,
                      left: 0,
                    }}
                  >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="forecast_date" />
                  <YAxis width="auto" domain={["auto", "auto"]} />
                  <Tooltip
                    formatter={(value: any, name: any) => [value, String(name).toUpperCase()]}
                    labelFormatter={(_: any, payload: any) =>
                      payload?.[0]?.payload?.timestamp_utc
                        ? formatDate(payload[0].payload.timestamp_utc)
                        : "-"
                    }
                  />
                  <Legend verticalAlign="top" align="center" height={28} />
                  {/* <Area
                    dataKey="o3MinMax"
                    fill="#a855f7"
                    stroke="#a855f7"
                    fillOpacity={0.12}
                  /> */}
                  <Area
                    dataKey="pm25MinMax"
                    fill="#ef4444"
                    stroke="#ef4444"
                    fillOpacity={0.12}
                  />
                  {/* <Area
                    dataKey="pm10"
                    fill="#eab308"
                    stroke="#eab308"
                    fillOpacity={0.12}
                  /> */}
                  <Area
                    dataKey="uviMinMax"
                    fill="#14b8a6"
                    stroke="#14b8a6"
                    fillOpacity={0.12}
                  />
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
                <Clock size={16} /> {formatDate(current?.timestamp_utc)}
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
                      <div key={`${row.timestamp_utc}-${index}`} className="record">
                        <div className="record-title">{formatDate(row.timestamp_utc)}</div>
                        <div className="record-grid">
                          <div>PM1: {row.pm1 ?? "-"}</div>
                          <div>PM2.5: {row.pm25 ?? "-"}</div>
                          <div>PM10: {row.pm10 ?? "-"}</div>
                          <div>Temp: {row.temperature_c ?? "-"} °C</div>
                          <div>Humidity: {row.humidity_pct ?? "-"} %</div>
                          <div>Station: {row.station_id ?? "-"}</div>
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
