#!/usr/bin/env python3
"""Generate the shared stop word registry for signal-mapper coverage metrics.

Categories are intentionally broad because false positives in the coverage
denominator are worse than over-filtering. The list combines:
- the standard NLTK English stop words (hardcoded; no nltk dependency)
- numeric literals and spelled-out quantities
- vendor/platform names that are context, not routing signals
- role/organization terms that describe people, not architectures
- time/frequency words that are too generic on their own
- legacy domain/business filler preserved from the existing registry so the
  generated output remains a superset of the prior hand-curated list
"""

from __future__ import annotations

import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "registry" / "stop-words.json"
DESCRIPTION = "Stop words excluded from signal-mapper coverage denominator."


def _lines(block: str) -> tuple[str, ...]:
    return tuple(sorted({line.strip() for line in block.splitlines() if line.strip()}))


# NLTK English stop words (179 terms). Keep the canonical forms even when the current tokenizer also relies on fragments like don/t.
STANDARD_ENGLISH_STOP_WORDS = _lines("""
a
about
above
after
again
against
ain
all
am
an
and
any
are
aren
aren't
as
at
be
because
been
before
being
below
between
both
but
by
can
couldn
couldn't
d
did
didn
didn't
do
does
doesn
doesn't
doing
don
don't
down
during
each
few
for
from
further
had
hadn
hadn't
has
hasn
hasn't
have
haven
haven't
having
he
her
here
hers
herself
him
himself
his
how
i
if
in
into
is
isn
isn't
it
it's
its
itself
just
ll
m
ma
me
mightn
mightn't
more
most
mustn
mustn't
my
myself
needn
needn't
no
nor
not
now
o
of
off
on
once
only
or
other
our
ours
ourselves
out
over
own
re
s
same
shan
shan't
she
she's
should
should've
shouldn
shouldn't
so
some
such
t
than
that
that'll
the
their
theirs
them
themselves
then
there
these
they
this
those
through
to
too
under
until
up
ve
very
was
wasn
wasn't
we
were
weren
weren't
what
when
where
which
while
who
whom
why
will
with
won
won't
wouldn
wouldn't
y
you
you'd
you'll
you're
you've
your
yours
yourself
yourselves
""")


# Numeric literals and spelled-out quantities that add denominator noise but do not indicate an architecture.
NUMERIC_STOP_WORDS = _lines("""
000
1
10
100
12
15
2
20
200
24
25
3
30
4
40
45
48
5
50
500
6
60
67
7
70
72
8
80
90
99
eight
five
four
half
hundred
million
nine
one
second
seven
six
ten
thousand
three
twice
two
""")


# Vendor, cloud, and product names that often appear as context but are not themselves routing signals.
VENDOR_AND_PLATFORM_STOP_WORDS = _lines("""
airbnb
amazon
aws
azure
confluent
databricks
dbt
fivetran
gcp
google
hadoop
hana
informatica
looker
microsoft
oracle
postgres
postgresql
salesforce
sap
snowflake
tableau
talend
teradata
uber
""")


# Job titles and generic stakeholder words that describe people rather than technical requirements.
ROLE_AND_ORGANIZATION_STOP_WORDS = _lines("""
analyst
analysts
architect
cdo
ceo
cfo
client
clients
committee
council
cto
customer
customers
department
departments
developer
developers
engineer
engineers
executive
executives
leadership
manager
managers
partner
partners
people
person
scientist
scientists
staff
stakeholder
stakeholders
team
teams
user
users
vendor
""")


# Schedule and cadence words that are useful context but are too generic to count as signal keywords by themselves.
TIME_AND_FREQUENCY_STOP_WORDS = _lines("""
daily
day
days
frequency
hour
hourly
hours
minute
minutes
month
months
morning
peak
period
time
times
week
weeks
year
years
""")


# Preserved domain/business filler from the legacy registry: generic verbs, nouns, adjectives, and process terms that commonly appear in problem statements but should not influence keyword coverage.
GENERIC_DOMAIN_CONTEXT_STOP_WORDS = _lines("""
able
access
across
actually
add
added
adds
adjustment
adjustments
allow
allowed
allows
already
also
always
among
another
answer
answers
anything
approach
around
ask
asked
asking
assess
assessing
automated
automatically
available
back
bad
based
basically
best
better
bi
blind
board
books
bought
broken
build
building
built
business
buy
buying
capacity
certain
certainly
chain
challenge
challenges
change
changed
changing
cheaper
choose
chose
chosen
claims
clinical
closed
closes
cluster
collect
collected
collecting
come
comes
coming
company
compare
compared
comparing
complete
complex
complicated
compute
concurrency
concurrent
consider
considered
considering
convince
cost
costs
could
create
created
creates
current
currently
data
decision
decisions
demand
depend
depending
depends
deploy
deployed
deploying
description
descriptions
different
discover
discovered
discovering
documentation
documented
downstream
easy
effort
end
ended
ends
enough
ensure
ensures
enter
entered
entering
entire
entries
entry
essentially
evaluate
evaluated
evaluating
even
every
everyone
everything
existing
expensive
faster
feature
features
field
finance
financial
find
finding
finds
first
fix
fixed
flag
flagged
fleet
found
full
generate
generated
generating
get
give
given
gives
go
goes
going
good
got
great
grow
growing
grows
handle
handled
handling
happen
happened
happens
hard
health
help
helped
helps
hire
hired
hiring
history
however
idea
identified
identify
identifying
implement
implemented
implementing
implements
important
impossible
improve
improved
improving
include
included
includes
including
incomplete
industrial
information
initiative
integrate
integrated
issue
issues
keep
keeps
know
known
knows
last
latest
launch
launched
launching
layer
layers
left
likely
line
lines
look
looking
looks
made
maintain
maintained
maintaining
make
makes
making
manage
management
manages
manufacturing
many
marketing
may
means
meant
mechanism
media
method
methods
might
migrate
migrated
migrating
modern
move
moved
moves
much
must
need
needs
never
new
next
nobody
node
nodes
nothing
old
operations
option
options
organization
particular
particularly
path
patient
per
plan
planned
planning
platform
possible
power
prefer
preferred
preferring
probably
problem
problems
process
product
production
products
program
project
provide
provided
provides
question
questions
read
ready
really
reason
reasons
receive
received
receiving
records
reduce
reduced
reducing
region
regional
relied
rely
relying
replace
replaced
replacing
request
requested
requesting
required
requires
requiring
resources
respond
response
result
resulting
results
retire
retired
rewrite
right
run
running
said
says
see
seeing
sees
sell
selling
send
sending
sent
separate
service
services
set
several
shall
show
showing
shown
shows
significant
significantly
simply
simultaneous
since
single
sit
sits
sitting
slower
social
sold
solution
solutions
someone
something
source
specific
specifically
spend
spending
spent
start
started
starts
still
store
strategy
stuck
supply
support
supported
supports
system
systems
take
taken
takes
taking
technique
techniques
tell
telling
tells
terrible
test
tested
testing
thing
things
told
tool
tools
track
tracking
tries
truly
try
trying
unable
unavailable
undocumented
unified
unsustainable
update
updated
updating
upstream
us
used
useless
uses
using
validate
validated
validating
vehicle
volume
volumes
want
wants
way
weather
whether
whole
within
without
work
worked
working
workload
workloads
works
worse
worst
would
write
""")


CATEGORY_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("standard_english", STANDARD_ENGLISH_STOP_WORDS),
    ("numbers", NUMERIC_STOP_WORDS),
    ("vendors_and_platforms", VENDOR_AND_PLATFORM_STOP_WORDS),
    ("roles_and_organizations", ROLE_AND_ORGANIZATION_STOP_WORDS),
    ("time_and_frequency", TIME_AND_FREQUENCY_STOP_WORDS),
    ("generic_domain_context", GENERIC_DOMAIN_CONTEXT_STOP_WORDS),
)


def _validate_categories() -> None:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for category_name, category_words in CATEGORY_ORDER:
        for word in category_words:
            previous = seen.get(word)
            if previous is not None:
                duplicates.append(f"{word}: {previous}, {category_name}")
            else:
                seen[word] = category_name
    if duplicates:
        joined = "; ".join(duplicates)
        raise ValueError(f"Duplicate stop words across categories: {joined}")


def build_stop_words() -> list[str]:
    _validate_categories()
    words: list[str] = []
    for _category_name, category_words in CATEGORY_ORDER:
        words.extend(category_words)
    return words


def build_stop_words_payload() -> dict[str, object]:
    return {
        "description": DESCRIPTION,
        "words": build_stop_words(),
    }


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(build_stop_words_payload(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH} ({len(build_stop_words())} words)")


if __name__ == "__main__":
    main()
