package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

const (
	groupID            = 218375169
	wordToCount        = "энвилоуп"
	postsPerRequest    = 100
	commentsPerRequest = 100
	batchSize          = 12
	token              = "token"
)

type Response struct {
	Response struct {
		Items []struct {
			ID   int    `json:"id"`
			Text string `json:"text"`
		} `json:"items"`
	} `json:"response"`
}

func fetchComments(postID int, commentsChan chan<- []string) {
	resp, err := http.Get(fmt.Sprintf("https://api.vk.com/method/wall.getComments?owner_id=-%d&post_id=%d&count=%d&access_token=%s&v=5.199", groupID, postID, commentsPerRequest, token))
	if err != nil {
		commentsChan <- nil
		return
	}
	defer resp.Body.Close()

	var data Response
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		commentsChan <- nil
		return
	}

	comments := make([]string, len(data.Response.Items))
	for i, item := range data.Response.Items {
		comments[i] = item.Text
	}
	commentsChan <- comments
}

func fetchPosts(offset int, totalCount *int, mu *sync.Mutex) {
	resp, err := http.Get(fmt.Sprintf("https://api.vk.com/method/wall.get?owner_id=-%d&count=%d&offset=%d&access_token=%s&v=5.199", groupID, postsPerRequest, offset, token))
	if err != nil {
		return
	}
	defer resp.Body.Close()

	var data Response
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return
	}

	var commentWg sync.WaitGroup
	commentsChan := make(chan []string)

	for _, post := range data.Response.Items {
		commentWg.Add(1)
		go func(postID int) {
			defer commentWg.Done()
			fetchComments(postID, commentsChan)
		}(post.ID)
	}

	go func() {
		commentWg.Wait()
		close(commentsChan)
	}()

	for comments := range commentsChan {
		if comments != nil {
			mu.Lock()
			*totalCount += countWord(comments, wordToCount)
			mu.Unlock()
		}
	}
}

func countWord(comments []string, word string) int {
	count := 0
	for _, comment := range comments {
		count += strings.Count(strings.ToLower(comment), strings.ToLower(word))
	}
	return count
}

func main() {
	fmt.Printf("[Запущено]\n")
	totalDuration := 0.0
	runs := 10

	for i := 0; i < runs; i++ {
		startTime := time.Now()
		var wg sync.WaitGroup
		var mu sync.Mutex
		totalCount := 0

		for j := 0; j < batchSize; j++ {
			wg.Add(1)
			go func(offset int) {
				defer wg.Done()
				fetchPosts(offset, &totalCount, &mu)
			}(j * postsPerRequest)
		}

		wg.Wait()

		duration := time.Since(startTime).Seconds()
		totalDuration += duration

		fmt.Printf("------%d/%d------\n'%s' упомянуто %d раз.\nВремя выполнения: %.2f секунд.\n", i+1, runs, wordToCount, totalCount, duration)
	}

	averageDuration := totalDuration / float64(runs)
	fmt.Printf("Среднее время выполнения: %.2f секунд.\n", averageDuration)
}
