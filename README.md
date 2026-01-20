# 🚀 Welcome to Air Quality Dashboard

Its a lazy Saturday and I get the bright idea, would it not be cool to have a nice UI for the GAIA A08 air quality tester I just finished setting up.  At this point I think maybe Claud would be a good choice and thats when I remebered hearing about Z.ai.  This would be the perfect challenge, needless to say I am impressed, as it gave me a FULLY DEBUGED solution that works localy.  Not so impressed with it's handling of updating the solution to use a given URL as the data source over the original mock data, but hey that was just the opportunity for Claud to shine.


``` bash
bun next build
docker-compose up -d
```

local [Air Quality Dashboard](http://localhost:8080/airQualityDashboard/index.html)


``` bash
docker-compose down
```
