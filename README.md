# todo-tickler
Automated tickler file processing

This python script will process a tickler.txt that has been created according
to the format specified in [GTD todo.txt : tickler file proposal] (https://medium.com/@criticalmind/gtd-todo-tickler-proposal-fe18ab324bca).  

Usage
-----

    ./weeklyreview.py  

Run this script in the directory containing your todo.txt file.  This script should be ideally run once a week during the weekend.  When it runs
it does the following.

*  Looks for the todo.txt, tickler.txt, done.txt and project.done.txt files in the current directory.  
*  Creates a list of all the projects that are currently "alive" and that do not have a next action assigned to them. It adds them in a file called review-YYYY-MM-DD.txt
*  Looks at the tickler.txt file and find out possible actionable items for the upcoming week and appends them to todo.txt

It supports all the repeat scenarios outlined in the blog post.
