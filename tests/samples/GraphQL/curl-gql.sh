#! /bin/sh
curl -i -H "Authorization: bearer <token>" -X POST -d " \
  { \
    \"query\": \" \
      query (\$number_of_repos: Int!) { \
        viewer { \
          name \
          repositories(last: \$number_of_repos) { \
            nodes { \
              name \
            } \
          } \
        } \
      } \", \
    \"variables\": { \
      \"number_of_repos\": 3
    } \
  } \
" https://api.github.com/graphql
