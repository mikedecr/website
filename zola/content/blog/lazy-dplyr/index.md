---
author: Michael DeCrescenzo
categories:
  - code
  - r
title: Dreams of a "Lazyverse"
subtitle: A delayed, functional interface for tidy data wrangling
date: '2023-07-06'
knitr:
  opts_chunk:
    eval: true
    include: true
    collapse: true
draft: false
---


This will maybe be a weird post.

This post explores a delayed-evaluation, function-forward interface for Tidyverse data manipulation, focusing primarily on `dplyr` verbs.
Instead of writing `data |> verb(args)`, it should be easier to capture `verb(args)` as its own expression, save it as a function, and later evaluate it on `data`.

In short, [partial application](https://en.wikipedia.org/wiki/Partial_application) of dplyr functions as a primary interface concept.

This post provides some less-than-ideal code to implement such an interface.
It is surely incomplete.
But the interface is interesting and appealing at least to me, a sometimes-R-user with some interest in functional programming.

## Good things about the Tidyverse

We like these features, and we want to preserve them as we extend the API:

-   **Uniform interfaces** mean functions are composable.
    Tidyverse functions typically map an argument of type T to an output of type T.
    `dplyr` and `tidyr` work on dataframes, and `stringr` on strings, `forcats` on factors...
-   **The forward pipe (`%>%` or `|>`)**.
    Instead of nested function calls `g(f(x))`, you can write a linear sequence of procedures `x |> f() |> g()`.
    This is now a feature of base R in part because the Tidyverse popularized it (but it did not invent it).
-   **Unquoted expressions** let you write "ergonomic" code that remains flexible.
    You can write `filter(data, var == value)` and trust that the `var` name is evaluated as a symbol in the `data` environment, even `var` is not a valid symbol in the environment where code is written.

But the Tidyverse needs something more, for me.

## Functional style

The Tidyverse is understood as a something of a "functional" interface for data manipulation in R: the interface is based on functions instead of classes.
This is broadly true of R when you compare it to something like Python.

But taking it one step higher, the Tidyverse style (or is it just the "pipeline" style?) doesn't exactly encourage you to write *your own* functions.

Take the following example.
I want to filter the `palmerpenguins` data to the "Adelie" species only.

``` r
library(palmerpenguins)
library(dplyr)
```

``` r
penguins |> 
    filter(species == "Adelie")
## # A tibble: 152 × 8
##    species island    bill_length_mm bill_depth_mm flipper_length_mm body_mass_g
##    <fct>   <fct>              <dbl>         <dbl>             <int>       <int>
##  1 Adelie  Torgersen           39.1          18.7               181        3750
##  2 Adelie  Torgersen           39.5          17.4               186        3800
##  3 Adelie  Torgersen           40.3          18                 195        3250
##  4 Adelie  Torgersen           NA            NA                  NA          NA
##  5 Adelie  Torgersen           36.7          19.3               193        3450
##  6 Adelie  Torgersen           39.3          20.6               190        3650
##  7 Adelie  Torgersen           38.9          17.8               181        3625
##  8 Adelie  Torgersen           39.2          19.6               195        4675
##  9 Adelie  Torgersen           34.1          18.1               193        3475
## 10 Adelie  Torgersen           42            20.2               190        4250
## # ℹ 142 more rows
## # ℹ 2 more variables: sex <fct>, year <int>
```

This works fine if I want to tie my functionality (drop all species but "Adelie") to my data (`penguins`).
But can I separate these steps?
Can I write a function (using `dplyr`) that filters on species, and then later apply that function to a dataframe?

Obviously I can do it this way:

``` r
adelie_only = function(d) {
    filter(d, species == "Adelie")
}
```

...which works, but it's verbose.
If I want to write a lot of these functions, basically half of my code is boilerplate.
I would prefer something closer to this:

``` r
# a "partial" recipe for filtering, regardless of the dataset.
adelie_only = delay(filter(species == "Adelie"))

# apply the filter to a dataset
adelie_only(penguins)
```

More abstractly, what I want is more separation of functions from data in the R pipeline style.
In some situation, I want to pass data `x` to functions `f`, `g`, and `h`.
But instead of writing this:

``` r
x |>
    f(...) |>
    g(...) |>
    h(...)
```

I want to write something like this:

``` r
# first argument omitted from each of these expressions
pipeline = compose(f(...), g(...), h(...))

# supply data to the ultimate function call
x |> pipeline()
```

`pipeline` is a function that captures unevaluated function calls on `f`, `g`, and `h` with their first arguments omitted.
Then I pass data `x` such that the data pass through the first argument of each function in the chain.

Why do I want this?
Because it should be easier to build a pipeline of expressions that can be re-used on different datasets.
I am thinking specically of examples like this:

``` r
# I could evaluate this function as-is
x |> pipeline()

# and I could also drop in extra steps j and k
x |> j() |> pipeline()
x |> k() |> pipeline()
```

Situations like this arise a lot on exploratory data analysis:

-   You summarize some data and then pivot it around to make it suitable for plotting.
-   You need to do the same summarize/pivot steps, but grouping the data in some way first.
    This doesn't replace the prior pipeline; it is an additional pipeline that reuses some of the same steps.
-   You need to do the same summarize/pivot steps once more, but now filtering out some observations.

As a researcher in finance, this often takes the form of computing some stats on some trades, and then seeing if the results hold up in different time periods, or how the results hold up when I filter to only trades that have certain features, and so on.
(I don't use R at work, but this pattern appears a lot anyway.)

I am just saying, it would be great to capture the summarize/pivot parts of this example as function(s) so that it's easier to re-use that code when you need to do prepend or append steps to this pipeline later on.

What can we do to make this possible?

## Tidy evaluation magic

What I want to do is replace a function call `f(x, ...)` with an expression that omits the first argument `f(...)`, delay the evaluation of the arguments `...`, and save a new function `g`.
Then I can call `g(x)` and get the same results as `f(x, ...)`.

This is basically partial function evaluation with support for lazily evaluated arguments.
(Functions like `mutate`, `select`, `filter`, etc. allow you to write *unquoted* variable names without throwing errors.)

We can do this with the `purrr::partial` function, which supports unquoted arguments.
Ideally we could do this without a dependency, but latching to the tidy ecosystem isn't so bad when it comes to supporting the evaluation patterns of these very popular APIs.

## Simple example, `delay_filter`

Let's create a function that filters only to the "Adelie" species, without requiring us to pass the data.

As a manually written function, it would look like this:

``` r
adelie_only = function(d) {
    filter(d, species == "Adelie")
}
```

But with `purrr::partial`, we would write this:

``` r
adelie_only = purrr::partial(filter, ...=, species == "Adelie")
```

The `...=` is a trick to deal with the fact that all of our provided arguments are positional arguments rather than named arguments.
We need to reserve one space on the left to pass the data frame, which is what we are doing with `...=`.

Just to show you it works:

``` r
adelie_only(penguins)
## # A tibble: 152 × 8
##    species island    bill_length_mm bill_depth_mm flipper_length_mm body_mass_g
##    <fct>   <fct>              <dbl>         <dbl>             <int>       <int>
##  1 Adelie  Torgersen           39.1          18.7               181        3750
##  2 Adelie  Torgersen           39.5          17.4               186        3800
##  3 Adelie  Torgersen           40.3          18                 195        3250
##  4 Adelie  Torgersen           NA            NA                  NA          NA
##  5 Adelie  Torgersen           36.7          19.3               193        3450
##  6 Adelie  Torgersen           39.3          20.6               190        3650
##  7 Adelie  Torgersen           38.9          17.8               181        3625
##  8 Adelie  Torgersen           39.2          19.6               195        4675
##  9 Adelie  Torgersen           34.1          18.1               193        3475
## 10 Adelie  Torgersen           42            20.2               190        4250
## # ℹ 142 more rows
## # ℹ 2 more variables: sex <fct>, year <int>
```

But writing the `partial` function call is still too much typing for me.
We can wrap this up into a function too.

``` r
delay_filter = function(...) {
    purrr::partial(filter, ...=, ...)
}

adelie_only = delay_filter(species == "Adelie")

adelie_only(penguins)
## # A tibble: 152 × 8
##    species island    bill_length_mm bill_depth_mm flipper_length_mm body_mass_g
##    <fct>   <fct>              <dbl>         <dbl>             <int>       <int>
##  1 Adelie  Torgersen           39.1          18.7               181        3750
##  2 Adelie  Torgersen           39.5          17.4               186        3800
##  3 Adelie  Torgersen           40.3          18                 195        3250
##  4 Adelie  Torgersen           NA            NA                  NA          NA
##  5 Adelie  Torgersen           36.7          19.3               193        3450
##  6 Adelie  Torgersen           39.3          20.6               190        3650
##  7 Adelie  Torgersen           38.9          17.8               181        3625
##  8 Adelie  Torgersen           39.2          19.6               195        4675
##  9 Adelie  Torgersen           34.1          18.1               193        3475
## 10 Adelie  Torgersen           42            20.2               190        4250
## # ℹ 142 more rows
## # ℹ 2 more variables: sex <fct>, year <int>
```

## Delay any function for pipe-friendly calling

If we really wanted to build an API atop this pattern at higher scale, we would like a tool to let us wrap any function like this.
So let's write `pipe_delay` which takes a function as its argument, and returns a partial function constructor as a value.

``` r
# verb -> (function(...) -> function(.data))
pipe_delay = function(verb) {
    function(...) {
        purrr::partial(verb, ...=, ...)
    }
}
```

And now we can create many delayed functions with this tool.

``` r
d_filter = pipe_delay(filter)
d_mutate = pipe_delay(mutate)
d_select = pipe_delay(select)
d_count = pipe_delay(count)
d_summarize = pipe_delay(summarize)
d_group_by = pipe_delay(group_by)
d_arrange = pipe_delay(arrange)
```

Some more trivial examples just to demonstrate what we have done.

``` r
select_species = d_select(species)
upper_species = d_mutate(species = toupper(species))

penguins |> select_species() |> upper_species()
## # A tibble: 344 × 1
##    species
##    <chr>  
##  1 ADELIE 
##  2 ADELIE 
##  3 ADELIE 
##  4 ADELIE 
##  5 ADELIE 
##  6 ADELIE 
##  7 ADELIE 
##  8 ADELIE 
##  9 ADELIE 
## 10 ADELIE 
## # ℹ 334 more rows
```

## The payoff: composable pipelines

This API lets us achieve the key benefits of pipeline style (stackable, linear code) while separating functions from data.
We define a pipeline over here, and evaluate it on multiple datasets over there.

The function definition piece evokes function composition in the purely mathematical sense.
I have two functions $f$ and $g$, and I want to chain them together.
I write the composition $g \cdot f$, which is a new function that means "do $g$ after $f$".

If we wanted, we could write some operators to help us build and read these compositions.

``` r
`%.%` = purrr::compose
`%;%` = purrr::partial(purrr::compose, .dir = "forward")
```

Or we could use the `purrr::compose` function directly.

## Bigger example with re-usable functions

I want to
- compute a ratio of bill length to depth
- group by species
- find the mean of this new ratio column.

First thing to note, I can write each of these steps as their own functions outside of the context where they are deployed, such as a library module (hint hint!).

``` r
by_species = d_group_by(species, .add = TRUE)

compute_length_to_depth = d_mutate(
    bill_length_to_depth = bill_length_mm / bill_depth_mm
)

# this function won't work unless this variable exists on the data we pass,
# but I can still define the fn wherever I want.
mean_bill_ratio = d_summarize(
    avg_bill_ratio = mean(bill_length_to_depth, na.rm = TRUE),
    .groups = "drop"
)
```

I can now write a "data pipeline" not as eager actions on data, but as functions that don't need to know anything about data.
Because there is no data here, I could also define this wherever I wanted.

``` r
# using "right" / "postfix" composition
species_mean_bill_ratio = compute_length_to_depth %;%
    by_species %;%
    mean_bill_ratio
```

Since my pipeline is a function, it is simple to apply it to any dataset I want.
For instance, here it is on the full dataset:

``` r
species_mean_bill_ratio(penguins)
## # A tibble: 3 × 2
##   species   avg_bill_ratio
##   <fct>              <dbl>
## 1 Adelie              2.12
## 2 Chinstrap           2.65
## 3 Gentoo              3.18
```

But let's say I wanted to group by year and sex as well, and compute the same pipeline.

``` r
penguins |>
    group_by(year, sex) |>
    species_mean_bill_ratio()
## # A tibble: 22 × 4
##     year sex    species   avg_bill_ratio
##    <int> <fct>  <fct>              <dbl>
##  1  2007 female Adelie              2.10
##  2  2007 female Chinstrap           2.61
##  3  2007 female Gentoo              3.22
##  4  2007 male   Adelie              2.05
##  5  2007 male   Chinstrap           2.66
##  6  2007 male   Gentoo              3.19
##  7  2007 <NA>   Adelie              2.07
##  8  2007 <NA>   Gentoo              3.11
##  9  2008 female Adelie              2.10
## 10  2008 female Chinstrap           2.66
## # ℹ 12 more rows
```

## Closing thoughts

The proposition of a delayed / functional approach to data manipulation is that you can define large transformations by defining many small transformations that can be chained, reordered, and so on.

What we want to achieve here is modularity.
Many of the "steps" in your pipeline are not dependent on the exact state of your data in the pipeline at the time that they are called, so why shouldn't I define these function apart from where they interact with specific data?
In this approach, your "pipeline" isn't a dataset being transformed; it is the recipe for transforming *any* dataset.
