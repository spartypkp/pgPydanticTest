# Instructions
Welcome to the pgtyped-pydantic test library. I plan to rename the Python side of things to something a little shorter, although I'm waiting for a stroke of inspiration.

In order to run this library, you will need to use npm to install pgtyped-pydantic, which is a node library which handles most of the heavy lifting for automatic type generation. This is my fork of pgtyped.

In your terminal, run:
1. npm install pgtyped-pydantic
2. npm install @pgtyped-pydantic/cli

Now clone this repository.
Make sure to fill in config.json with your db config. Touching anything but the DB config is guranteed to break your shit. Everything else is WIP, so careful.

You will be testing writing SQL queries within the test.py file.
In order to test automatic typing within test.py you need to follow this order:

1. Run sql_transformer.py. It will show debug messages and watch for changes in the repo.
2. Edit test.py. I have initialized the repo to be ready to automatically generate types for a diverse set of queries, which will show off some of the semi-automatic paramter expansions. I have edited the functionality of pgtyped to expand "Objects" into "Pydantic Models". 
3. Save test.py with an extra comment or some BS, and watch the magic happen.
4. Try and execute the code inline, which will break for some dynamic queries. **See Below**

# Limitation
Somehow in my Sunday coding sesh today this week it completely slipped my mind that I had not solved SQL query execution yet. I have no reliable way to dynamically build and run SQL queries with inserted paramters. I have done much hard thinking and have come up with some possible work arounds, which I'm going to list here:
1. Convert SQL query annotation to TS Query Annotation, as defined by the Original Pgtyped Library.
- Pgtyped already allows for this dynamic query execution. However, it must be in TS files, and within a very strict format.
- Running queries would mean ANOTHER npx call to pgtyped, this time passing forward HUGE amounts of structured data as raw strings. Lots of work would need to go into reformatting Pydantic model parameters into typescript.
- If anyone is counting, this will extend the horrific language tranlsation chain to: Python -> Inline SQL -> Temp SQL File for npx input -> Typescript Representation of SQL in PGTyped -> Raw Text From npx output -> Pydantic Models -> Raw Text to npx input again -> Typescript -> Raw text from npx output again -> Pydantic Models. I'd rather KMS.
2. Stop being a little bitch and truly overhaul the pgtyped Query & Parser library to native Python, using psycopg.
- It's most definitely doable, and will allow for dealing with Pydantic models easier.
- It will be an absolute challenge. It will take a long time. 
- I will be creating my own custom Query Builder.
- I can fix all the stupid notations from pgtyped, optimized and redisgned for pydantic.
3. Find an intermediate solution for a native Python Query Builder.
- This is probably the sane choice.
- I need to bridge (Raw Query w Placeholders, Params) -> (Finalized Dynamic Query w Params Inserted)
- I'm up for suggestions, and probably will need a lot more research.
4. Be happy with providing dynamic typing Alone. The world is a scary place, users can execute their SQL queries on their own.
- This is giving up. I don't want to give up. I am lazy, I want to automatically run my own queries.
- I refuse to be happy. With this. 


Anyways, lots of work left to be done. If you have tips for my SQL query execution obstacle, please lmk.