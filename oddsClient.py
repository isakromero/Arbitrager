import requests
from collections import defaultdict
import queue

EXTRA_API_KEYS = [
    "f2d7950f62eb985926d74b3458f49f97", # real
    "9f494394c6cfd78589b097d92e45fdb5",
    "924f72f3d14ddea984546cd865423d6e"
]
API_KEY = EXTRA_API_KEYS[1]
BASE_URL = "https://api.the-odds-api.com/"

class OddsClient:

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key

    def get_request(self, path, **params):
        url = BASE_URL + path
        resp = requests.get(url, params={
            "apiKey": self.api_key,
            **params,
        })
        return resp
    
    def get_in_season_sports(self):
        path = "v4/sports"
        resp = self.get_request(path)
        return resp.json()
    
    def get_odds_for_sport(self, sport_key, regions="us", odds_format="decimal", bookmakers="betmgm,draftkings,fanduel"):
        path = f"v4/sports/{sport_key}/odds"

        resp = self.get_request(path,
            regions = regions,
            markets =  "h2h",
            oddsFormat = odds_format,
            bookmakers = bookmakers
        )

        return resp.json()
    
    def print_sports_by_category(self):
        sports = self.get_in_season_sports()
        sport_by_category = defaultdict(lambda: [])

        for sport in sports:
            sport_object = Sport(**sport)
            sport_by_category[sport["group"]].append(sport_object)

        for category, sports in sport_by_category.items():
            print(f"{category}:")
            for sport in sports:
                print(f"\t{str(sport)}")
    
class Sport:
    # {'key': 'americanfootball_cfl', 'group': 'American Football', 'title': 'CFL', 'description': 'Canadian Football League', 'active': True, 'has_outrights': False}
    def __init__(self, **params):
        self.key = params["key"]
        self.group = params["group"]
        self.title = params["title"]
        self.description = params["description"]
        self.active = params["active"]
        self.has_outrights = params["has_outrights"]

    def is_active(self):
        return self.active

    def __str__(self):
        return f"{self.title} with key {self.key} - {self.description}"

class EventOdds:
    # Raw Object
    # {'id': '95bb0608f6faefc4417d3263e2ce9af4', 'sport_key': 'cricket_test_match', 'sport_title': 'Test Matches', 'commence_time': '2024-08-10T13:30:00Z', 'home_team': 'West Indies', 'away_team': 'South Africa', 'bookmakers': [{'key': 'draftkings', 'title': 'DraftKings', 'last_update': '2024-08-10T17:24:38Z', 'markets': [{'key': 'h2h', 'last_update': '2024-08-10T17:24:38Z', 'outcomes': [{'name': 'South Africa', 'price': 2000}, {'name': 'West Indies', 'price': 3500}, {'name': 'Draw', 'price': -20000}]}]}]}
    def __init__(self, **params):
        self.id = params["id"]
        self.sport_key = params["sport_key"]
        self.sport_title = params["sport_title"]
        self.commence_time = params["commence_time"]
        self.bookmakers = params["bookmakers"]
        self.markets = None
        self.generate_markets_data()


    def __str__(self):
        return f"{self.sport_title}"
    
    def group_bets_by_type(self):
        bets = dict()

        for bookie in self.bookmakers:
            bets[bookie["key"]] = bookie["markets"][0]["outcomes"]
        
    def generate_markets_data(self):
        if self.markets:
            return
        
        self.markets = dict()

        for bookie in self.bookmakers:
            markets = bookie["markets"]

            for market in markets:
                bet_type = market["key"]
                if bet_type not in self.markets:
                    self.markets[bet_type] = Market(self.sport_title, bet_type)

                for outcome in market["outcomes"]:
                    self.markets[bet_type].add_outcome(outcome["name"], outcome["price"], bookie["title"])

    def print_markets(self):
        for market in self.markets:
            print(self.markets[market])


class Market():
    def __init__(self, event_name, bet_type):
        self.event_name = event_name
        self.bet_type = bet_type
        self.outcomes = defaultdict(lambda: [])

    def add_outcome(self, outcome, odds, bookmaker):
        if bookmaker == "MyBookie.ag" or bookmaker == "Bovada":
            return 
        
        self.outcomes[outcome].append((odds, bookmaker))
        self.outcomes[outcome].sort()
        
    def __str__(self):
        output = f"""{self.event_name} - {self.bet_type}\n"""
        for outcome in self.outcomes:
            if len(self.outcomes[outcome]) == 0:
                continue

            odds = self.outcomes[outcome]
            output += f"\t{outcome}: {odds[0]} to {odds[-1]}\n"

        best_delta , _= self.get_biggest_delta()
        output += f"\tBest Delta: {best_delta}"
            
        return output

    def get_biggest_delta(self):
        max_delta = 0
        
        for outcome in self.outcomes:
            min_odds = self.outcomes[outcome][0][0]
            max_odds = self.outcomes[outcome][-1][0]
            delta = abs(max_odds - min_odds)
            if delta > max_delta:
                max_delta = delta

        return (max_delta, self)

    def get_arbitrage(self):
        arb = 1 

        for outcome in self.outcomes:
            arb -= 1/self.outcomes[outcome][-1][0]

        return arb

if __name__ == "__main__":
    client = OddsClient()
    resp = client.get_odds_for_sport('upcoming')
    
    best_deltas = []

    for event in resp:
        event_object = EventOdds(**event)
        # print(str(event_object))
        # event_object.print_markets()

        for market in event_object.markets:
            delta, market_object = event_object.markets[market].get_biggest_delta()
            arb = market_object.get_arbitrage()

            best_deltas.append((arb, delta, market_object))
            # if delta > best_delta[0]:
            #     best_delta = (delta, market_object)

    best_deltas.sort(key=lambda x: x[0])
    for arb, delta, market in best_deltas:
        print(market)
        print(f"\tBest Delta: {delta}")
        print(f"\tArbitrage: {arb}")





