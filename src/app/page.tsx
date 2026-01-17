'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Activity, Wind, Droplets, Gauge, MapPin, Clock, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts'

// Types
interface PollutantData {
  v: number
}

interface IAQI {
  co: PollutantData
  h: PollutantData
  no2: PollutantData
  o3: PollutantData
  p: PollutantData
  pm25: PollutantData
  so2: PollutantData
  t: PollutantData
  w: PollutantData
}

interface Attributions {
  url: string
  name: string
  logo?: string
}

interface City {
  geo: [number, number]
  name: string
  url: string
  location: string
}

interface Time {
  s: string
  tz: string
  v: number
  iso: string
}

interface ForecastEntry {
  avg: number
  day: string
  max: number
  min: number
}

interface ForecastData {
  o3: ForecastEntry[]
  pm10: ForecastEntry[]
  pm25: ForecastEntry[]
  uvi: ForecastEntry[]
}

interface AirQualityData {
  aqi: number
  idx: number
  attributions: Attributions[]
  city: City
  dominentpol: string
  iaqi: IAQI
  time: Time
  forecast: {
    daily: ForecastData
  }
  debug: {
    sync: string
  }
}

interface APIResponse {
  status: string
  data: AirQualityData
}

// Helper functions
const getAQIStatus = (aqi: number) => {
  if (aqi <= 50) return { status: 'Good', color: 'bg-green-500', icon: CheckCircle, description: 'Air quality is satisfactory' }
  if (aqi <= 100) return { status: 'Moderate', color: 'bg-yellow-500', icon: AlertCircle, description: 'Acceptable for most people' }
  if (aqi <= 150) return { status: 'Unhealthy for Sensitive', color: 'bg-orange-500', icon: AlertTriangle, description: 'Sensitive groups may experience effects' }
  if (aqi <= 200) return { status: 'Unhealthy', color: 'bg-red-500', icon: AlertTriangle, description: 'Everyone may experience health effects' }
  if (aqi <= 300) return { status: 'Very Unhealthy', color: 'bg-purple-600', icon: AlertTriangle, description: 'Health alert: everyone at risk' }
  return { status: 'Hazardous', color: 'bg-red-900', icon: AlertTriangle, description: 'Emergency conditions: entire population at risk' }
}

const getPollutantName = (key: string): string => {
  const names: Record<string, string> = {
    pm25: 'PM2.5',
    pm10: 'PM10',
    o3: 'Ozone (O3)',
    no2: 'Nitrogen Dioxide',
    so2: 'Sulfur Dioxide',
    co: 'Carbon Monoxide',
    h: 'Humidity',
    t: 'Temperature',
    p: 'Pressure',
    w: 'Wind Speed'
  }
  return names[key] || key.toUpperCase()
}

const getPollutantUnit = (key: string): string => {
  const units: Record<string, string> = {
    pm25: 'µg/m³',
    pm10: 'µg/m³',
    o3: 'µg/m³',
    no2: 'µg/m³',
    so2: 'µg/m³',
    co: 'mg/m³',
    h: '%',
    t: '°C',
    p: 'hPa',
    w: 'm/s'
  }
  return units[key] || ''
}

const isWeatherData = (key: string): boolean => {
  return ['h', 't', 'p', 'w'].includes(key)
}

export default function AirQualityDashboard() {
  const [data, setData] = useState<AirQualityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simulate API call with mock data
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        
                // Fetch real air quality data from WAQI API
        const response = await fetch(
          'https://api.waqi.info/feed/here/?token=a024603beff930712268430f02e9c173d367923a'
        )
        
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        
        const apiData: APIResponse = await response.json()
        
        if (apiData.status !== 'ok') {
          throw new Error('API returned an error status')
        }
        
        setData(apiData.data)
      } catch (err) {
        setError('Failed to load air quality data. Please try again.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          {/* Header Skeleton */}
          <div className="mb-8">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>

          {/* AQI Display Skeleton */}
          <Card className="mb-6">
            <CardContent className="p-8">
              <div className="flex items-center justify-between">
                <div>
                  <Skeleton className="h-12 w-48 mb-4" />
                  <Skeleton className="h-32 w-48 mb-4" />
                  <Skeleton className="h-6 w-64" />
                </div>
                <Skeleton className="h-40 w-40 rounded-full" />
              </div>
            </CardContent>
          </Card>

          {/* Cards Grid Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-24 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center px-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data) return null

  const aqiInfo = getAQIStatus(data.aqi)
  const StatusIcon = aqiInfo.icon

  // Chart configuration
  const chartConfig: ChartConfig = {
    aqi: {
      label: 'AQI',
      color: 'hsl(var(--chart-1))',
    },
    min: {
      label: 'Min',
      color: 'hsl(var(--chart-4))',
    },
    max: {
      label: 'Max',
      color: 'hsl(var(--chart-5))',
    },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-2">
            Air Quality Dashboard
          </h1>
          <p className="text-muted-foreground text-lg">
            Real-time air quality monitoring and forecasts
          </p>
        </header>

        {/* City Info */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-muted-foreground" />
                <span className="text-2xl font-semibold">{data.city.name}</span>
              </div>
              <Separator orientation="vertical" className="h-8" />
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Last updated: {new Date(data.time.iso).toLocaleString()}</span>
              </div>
              <Separator orientation="vertical" className="h-8" />
              <Badge variant="secondary" className="text-sm">
                ID: {data.idx}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Main AQI Display */}
        <Card className="mb-6 overflow-hidden">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="flex-1">
                <h2 className="text-2xl font-semibold mb-4">Air Quality Index</h2>
                <div className="flex items-baseline gap-3 mb-4">
                  <span className="text-7xl font-bold text-foreground">{data.aqi}</span>
                  <Badge className="text-lg px-4 py-1 h-fit">
                    {aqiInfo.status}
                  </Badge>
                </div>
                <p className="text-muted-foreground text-lg flex items-start gap-2">
                  <StatusIcon className="h-5 w-5 mt-0.5" />
                  {aqiInfo.description}
                </p>
                <p className="text-sm text-muted-foreground mt-3">
                  Dominant pollutant: <span className="font-medium text-foreground">{getPollutantName(data.dominentpol)}</span>
                </p>
              </div>

              {/* AQI Progress Circle */}
              <div className="relative">
                <div className={`w-40 h-40 rounded-full ${aqiInfo.color} flex items-center justify-center shadow-2xl`}>
                  <div className="text-white text-center">
                    <Activity className="h-12 w-12 mx-auto mb-1" />
                    <span className="text-sm font-medium">AQI</span>
                  </div>
                </div>
              </div>
            </div>

            {/* AQI Scale Bar */}
            <div className="mt-8">
              <div className="h-4 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 via-red-500 via-purple-600 to-red-900 relative">
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-0.5 h-6 bg-foreground transform -translate-x-1/2"
                  style={{ left: `${Math.min((data.aqi / 500) * 100, 100)}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>0 (Good)</span>
                <span>500 (Hazardous)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs for Pollutants and Weather */}
        <Tabs defaultValue="pollutants" className="mb-8">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="pollutants">Air Pollutants</TabsTrigger>
            <TabsTrigger value="weather">Weather Conditions</TabsTrigger>
          </TabsList>

          {/* Pollutants Tab */}
          <TabsContent value="pollutants">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Object.entries(data.iaqi)
                .filter(([key]) => !isWeatherData(key))
                .map(([key, value]) => {
                  const name = getPollutantName(key)
                  const unit = getPollutantUnit(key)
                  const isDominant = key === data.dominantpol
                  const percentage = Math.min((value.v / 200) * 100, 100)

                  return (
                    <Card key={key} className={`transition-all hover:shadow-lg ${isDominant ? 'ring-2 ring-primary ring-offset-2' : ''}`}>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg flex items-center justify-between">
                          {name}
                          {isDominant && (
                            <Badge variant="secondary" className="text-xs">
                              Dominant
                            </Badge>
                          )}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="mb-4">
                          <span className="text-4xl font-bold text-foreground">{value.v}</span>
                          <span className="text-sm text-muted-foreground ml-1">{unit}</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </CardContent>
                    </Card>
                  )
                })}
            </div>
          </TabsContent>

          {/* Weather Tab */}
          <TabsContent value="weather">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Wind className="h-5 w-5" />
                    Wind Speed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-foreground mb-1">{data.iaqi.w.v}</div>
                  <div className="text-sm text-muted-foreground">m/s</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Droplets className="h-5 w-5" />
                    Humidity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-foreground mb-1">{data.iaqi.h.v}</div>
                  <div className="text-sm text-muted-foreground">%</div>
                  <Progress value={data.iaqi.h.v} className="h-2 mt-3" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Gauge className="h-5 w-5" />
                    Pressure
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-foreground mb-1">{data.iaqi.p.v}</div>
                  <div className="text-sm text-muted-foreground">hPa</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Temperature
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-foreground mb-1">{data.iaqi.t.v}</div>
                  <div className="text-sm text-muted-foreground">°C</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Forecast Charts */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>7-Day Forecast</CardTitle>
            <CardDescription>Predicted air quality for the next week</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="pm25">
              <TabsList className="mb-6">
                <TabsTrigger value="pm25">PM2.5</TabsTrigger>
                <TabsTrigger value="pm10">PM10</TabsTrigger>
              </TabsList>

              <TabsContent value="pm25">
                <ChartContainer config={chartConfig} className="h-[300px] w-full">
                  <LineChart data={data.forecast.daily.pm25}>
                    <CartesianGrid vertical={false} />
                    <XAxis 
                      dataKey="day" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { weekday: 'short' })}
                    />
                    <YAxis />
                    <ChartTooltip 
                      content={<ChartTooltipContent />}
                      labelFormatter={(value) => new Date(value as string).toLocaleDateString()}
                    />
                    <Line 
                      dataKey="avg" 
                      stroke="var(--color-aqi)" 
                      strokeWidth={2}
                      dot={{ fill: "var(--color-aqi)" }}
                    />
                    <Line 
                      dataKey="min" 
                      stroke="var(--color-min)" 
                      strokeWidth={1}
                      strokeDasharray="4"
                      dot={{ fill: "var(--color-min)" }}
                    />
                    <Line 
                      dataKey="max" 
                      stroke="var(--color-max)" 
                      strokeWidth={1}
                      strokeDasharray="4"
                      dot={{ fill: "var(--color-max)" }}
                    />
                  </LineChart>
                </ChartContainer>
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center">
                  {data.forecast.daily.pm25.map((day, index) => (
                    <div key={index} className="p-2 rounded-md bg-muted/50">
                      <div className="text-xs text-muted-foreground mb-1">
                        {new Date(day.day).toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="text-lg font-semibold text-foreground">{day.avg}</div>
                      <div className="text-xs text-muted-foreground">
                        {day.min}-{day.max}
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="pm10">
                <ChartContainer config={chartConfig} className="h-[300px] w-full">
                  <LineChart data={data.forecast.daily.pm10}>
                    <CartesianGrid vertical={false} />
                    <XAxis 
                      dataKey="day" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { weekday: 'short' })}
                    />
                    <YAxis />
                    <ChartTooltip 
                      content={<ChartTooltipContent />}
                      labelFormatter={(value) => new Date(value as string).toLocaleDateString()}
                    />
                    <Line 
                      dataKey="avg" 
                      stroke="var(--color-aqi)" 
                      strokeWidth={2}
                      dot={{ fill: "var(--color-aqi)" }}
                    />
                    <Line 
                      dataKey="min" 
                      stroke="var(--color-min)" 
                      strokeWidth={1}
                      strokeDasharray="4"
                      dot={{ fill: "var(--color-min)" }}
                    />
                    <Line 
                      dataKey="max" 
                      stroke="var(--color-max)" 
                      strokeWidth={1}
                      strokeDasharray="4"
                      dot={{ fill: "var(--color-max)" }}
                    />
                  </LineChart>
                </ChartContainer>
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center">
                  {data.forecast.daily.pm10.map((day, index) => (
                    <div key={index} className="p-2 rounded-md bg-muted/50">
                      <div className="text-xs text-muted-foreground mb-1">
                        {new Date(day.day).toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="text-lg font-semibold text-foreground">{day.avg}</div>
                      <div className="text-xs text-muted-foreground">
                        {day.min}-{day.max}
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Attributions */}
        <Card>
          <CardHeader>
            <CardTitle>Data Sources</CardTitle>
            <CardDescription>Air quality data provided by</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.attributions.map((attr, index) => (
                <div key={index} className="flex items-center gap-3">
                  <Badge variant="outline" className="font-normal">
                    {attr.name}
                  </Badge>
                  <a
                    href={attr.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    View Source →
                  </a>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <footer className="mt-12 py-6 text-center text-sm text-muted-foreground border-t">
          <p>Air Quality Dashboard • Real-time environmental monitoring</p>
        </footer>
      </div>
    </div>
  )
}
