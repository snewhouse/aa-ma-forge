library(dplyr)

clean_visits = function(df) {
  df %>% filter(!is.na(visit_date)) %>% mutate(year = format(visit_date, "%Y"))
}
