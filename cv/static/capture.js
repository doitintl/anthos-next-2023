async function capture() {
    try {
      const response = await fetch(`/capture`, {
        method: 'GET',
      });
      if (response.ok) {
        const text = await response.json();
        console.log(text);
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
      const response = await fetch(`/messages`, {
        method: 'GET',
      });
      if (response.ok) {
        const text = await response.json();
        console.log(text);
        document.getElementById("messages").innerHTML = text;
      }
      else {
        window.alert('Something went wrong... Please try again!');
      }
    } catch (err) {
      console.log(`Error when getting messages: ${err}`);
      window.alert('Something went wrong... Please try again!');
    }
}