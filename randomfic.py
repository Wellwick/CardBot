import random

from ff.fiction import Story, Chapter, User

with open("testing.txt", "r") as f:
    ids = f.readlines()

linecount=3

story = Story(id=random.choice(ids))
story.download_data()

chapter_val = random.randrange(story.chapter_count) + 1

chapter = Chapter(story_id=story.id, chapter=chapter_val)


author = User(id=story.author_id)
author.download_data()

print(story.title + " by " + author.username)
print("Link: " + story.url)
print("Chapter " + str(chapter_val))
lines = chapter.text.split("\n")

guess_lines = []
current_line = ""
for line in lines:
    if len(line.strip()) == 0:
        continue
    if line.strip()[-1] not in [".", "!", "?", '"', "'", ")", "]"]:
        current_line += line.strip() + " "
    elif current_line != "":
        current_line += line.strip()
        guess_lines += [ current_line ]
        current_line = ""
    else:
        guess_lines += [ line ]
if linecount >= len(guess_lines):
    print("\n".join(guess_lines))
else:
    lineIndex = random.randrange(len(guess_lines)-linecount)
    print("\n".join(guess_lines[lineIndex:lineIndex+linecount]))

