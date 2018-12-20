# Stably-Coding-Task

Some of the integer constants in the main python file may seems magical, they are 
just a good default for getting the entire supply history without having so many 
data points it takes forever to load.

Current issue is the x-axis of the graph displays the block instead of the timestamp.
I am working on making this a timestamp instead but there does not seem to be
functionality in the web3 api to get the most recent block from a timestamp or check
when a block was the most recent block.
