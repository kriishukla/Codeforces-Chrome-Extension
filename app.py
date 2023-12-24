import json
import datetime as dt
import requests
import random

completedProblems = {}

def userDetails(codeforcesHandle, clearPastProblems):
    url = requests.get(f'https://codeforces.com/api/user.info?handles={codeforcesHandle}')
    jsonData = url.json()
    data = json.dumps(jsonData)
    codeforcesHandle = json.loads(data)
    if codeforcesHandle['status'] != "OK":
        return False
    if clearPastProblems:
        completedProblems.clear()
    return codeforcesHandle['result'][0]

def convertUnixTime(unixtime):
    date = dt.datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d')
    time = dt.datetime.fromtimestamp(unixtime).strftime('%H:%M:%S')
    date_time_obj = dt.datetime.strptime(date+" "+time, '%Y-%m-%d %H:%M:%S')
    time = date_time_obj.time()
    time = str((dt.datetime.combine(dt.date(1, 1, 1), time) +
                dt.timedelta(hours=5, minutes=30)).time())
    return date+" "+time

def convertToHour(secondsTime):
    return str(dt.timedelta(seconds=secondsTime))

def contestDetails():
    url = requests.get('https://codeforces.com/api/contest.list')
    jsonData = url.json()
    data = json.dumps(jsonData)
    contests = json.loads(data)
    contestList = []
    count = 0
    for contest in contests['result']:
        if contest['phase'] == "FINISHED":
            break
        else:
            contest['startTimeSeconds'] = convertUnixTime(
                contest['startTimeSeconds'])
            contest['durationSeconds'] = convertToHour(
                contest['durationSeconds'])
            contestList.append(contest)
            count += 1
    contestList = contestList[::-1]
    return contestList[0:5]

def getTags(codeforcesHandle, rank):
    url = requests.get(f'https://codeforces.com/api/user.status?handle={codeforcesHandle}')
    jsonData = url.json()
    submissions = jsonData.get('result', [])
    
    # Filter submissions with the specified tag and only consider solved problems
    solved_problems = [problem['problem'] for problem in submissions if problem['verdict'] == 'OK']
    
    visitedProblems = {}
    wrongSubmissions = {}

    if rank == 'pupil':
        minSolvedCount = 8000
        maxSolvedCount = 18000
    else:
        minSolvedCount = 0
        maxSolvedCount = 35000

    for problem in solved_problems:
        if problem['name'] in visitedProblems:
            continue
        visitedProblems[problem['name']] = 1
        for tag in problem.get('tags', []):
            if tag not in wrongSubmissions:
                wrongSubmissions[tag] = 1
            else:
                wrongSubmissions[tag] += 1

    weakTags = {}
    for tag in sorted(wrongSubmissions.items(), key=lambda x: x[1], reverse=True):
        average_rating = getAverageRatingOfLastSolvedProblems(codeforcesHandle, tag[0], count=10)
        weakTags[tag[0]] = {'problems': getProblems(tag[0], rank, minSolvedCount, maxSolvedCount), 'average_rating': average_rating}
        if len(weakTags) == 6:
            break
    return weakTags

def getProblems(tag, rank, minSolvedCount, maxSolvedCount):
    problems = []
    url = requests.get(f'https://codeforces.com/api/problemset.problems?tags={tag}')
    jsonData = url.json()
    allData = jsonData.get('result', {})
    allProblems = allData.get('problems', [])
    allproblemStatistics = allData.get('problemStatistics', [])

    count = 0
    lengthOfProblemSet = len(allProblems)
    j = 0
    alreadySuggested = {}

    while j < lengthOfProblemSet:
        j += 1
        i = random.randint(0, lengthOfProblemSet - 1)
        if "points" in allProblems[i] and allProblems[i]['points'] <= 1000:
            continue
        elif allProblems[i]['index'] == 'A':
            continue
        if tag in allProblems[i].get('tags', []):
            if (allProblems[i]['name'] not in alreadySuggested) and (allProblems[i]['name'] not in completedProblems) and allproblemStatistics[i]['solvedCount'] >= minSolvedCount and allproblemStatistics[i]['solvedCount'] <= maxSolvedCount:
                alreadySuggested[allProblems[i]['name']] = 1
                tempList = []
                tempList.append(allProblems[i]['name'])
                tempList.append(f'https://codeforces.com/problemset/problem/{allProblems[i]["contestId"]}/{allProblems[i]["index"]}')
                problems.append(tempList)
                count += 1
        if count == 6:
            break
    return problems

def getAverageRatingOfLastSolvedProblems(codeforcesHandle, tag, count):
    url = requests.get(f'https://codeforces.com/api/user.status?handle={codeforcesHandle}&from=1&count=100000')
    jsonData = url.json()
    submissions = jsonData.get('result', [])

    # Filter submissions with the specified tag and only consider solved problems
    solved_problems = [problem['problem'] for problem in submissions if problem['verdict'] == 'OK' and tag in problem.get('tags', [])]

    # Take the last 'count' solved problems
    last_solved_problems = solved_problems[-count:]

    # Calculate the average rating
    if last_solved_problems:
        average_rating = sum(problem.get('rating', 0) for problem in last_solved_problems) / len(last_solved_problems)
        return average_rating
    else:
        return 0

def main():
    codeforcesHandle = input("Enter Codeforces handle: ")
    clearPastProblems = input("Clear past problems? (yes/no): ").lower() == 'yes'

    user_info = userDetails(codeforcesHandle, clearPastProblems)

    if user_info:
        print("\nUser Information:")
        print("Handle:", user_info['handle'])
        print("Rank:", user_info['rank'])

        weak_tags = getTags(user_info['handle'], user_info['rank'])
        print("\nWeak Tags:")
        for tag, info in weak_tags.items():
            print(f"{tag}:")
            print("  Problems:", info['problems'])
            print("  Average Rating of Last 10 Solved Problems:", info['average_rating'])

    else:
        print("Failed to fetch user details.")

if __name__ == "__main__":
    main()
    
