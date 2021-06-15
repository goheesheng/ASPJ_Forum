function postVote(button) {
  var voteValue = button.getAttribute("data-vote");
  var postID = button.getAttribute("data-post");

  fetch('/postVote', {
    headers: new Headers({
      "content-type": "application/json"
    }),
    method: 'POST',
    body: JSON.stringify({
        "voteValue": voteValue,
        "postID": postID
    })
  })

  .then(function (response) { // At this point, Flask has printed our JSON
    response.json().then(function(data) {
      if (response.status === 401) {
        location.reload();
      }

      else {
        if (data['toggleUpvote']==true) {
          document.querySelector('#post-votes-' + data['postID'] + ' [data-vote="1"] i.fa-arrow-up').classList.toggle('active');
        }

        if (data['toggleDownvote']) {
          document.querySelector('#post-votes-' + data['postID'] + ' [data-vote="-1"] i.fa-arrow-down').classList.toggle('active');
        }

        document.querySelector('#post-votes-' + data['postID'] + ' #postTotalVotes').innerText = data['updatedVoteTotal'];
      }
    });
  }).catch(function (error) {
      console.log("Fetch error: " + error['message']);
  });
}
