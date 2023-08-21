async function capture() {
    try {
      const response = await fetch(`/capture`, {
        method: 'GET',
      });
      if (response.ok) {
        const text = await response.json();
        console.log(text);
        localStorage.setItem("image_name", text.image_name)
        window.location.reload();
      }
      else {
        window.alert('Something went wrong... Please try again!');
      }
    } catch (err) {
      console.log(`Error when capturing image: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
}

async function clear() {
    try {
      const response = await fetch(`/clear`, {
        method: 'GET',
      });
      if (response.ok) {
        const text = await response.json();
        console.log(text);
        document.getElementById("messages").innerHTML = "";
      }
      else {
        window.alert('Something went wrong... Please try again!');
      }
    } catch (err) {
      console.log(`Error when clearing image: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
}

async function messages() {
    try {
      file_name = localStorage.getItem("image_name")
      const response = await fetch(`/messages/${file_name}`, {
        method: 'GET',
      });
      if (response.ok) {
        const json_response = await response.json();
        console.log(json_response);
        document.getElementById("messages").innerHTML = json_response["messages"];
      }
      else {
        window.alert('Something went wrong... Please try again!');
      }
    } catch (err) {
      console.log(`Error when getting messages: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
}